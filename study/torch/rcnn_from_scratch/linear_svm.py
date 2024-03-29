'''
Support Vector Machine에는 선형회귀와 hinge_loss가 포함되어있다.

(1) negative sample mining
: 모델이 예측에 실패하는 어려운 샘플들을 모으는 기법
  배경에 해당하는 negative sample이 훨씬 많은 클래스 불균형으로 인해 
  객체로 인식했지만 실제로는 배경인 경우가 많다. (False Positive)
  -> False Positive sample을 학습 과정에서 추가하여 재학습하면 더욱 강건한 모델을 얻을 수 있다.

    1. 초기 훈련 세트 설정 : 양과 음 1:1
    2. 각 훈련 라운드가 완료된 후 분류기는 나머지 음성 샘플을 탐지하는데 사용
    3. 분류기를 다시 학습시키고 탐지 정확도가 수렴되기 시작할 때까지 2단계를 반복
(2) 훈련 매개변수
    - lr : 1e-4
    - momentum : 0.9
    - iter : 10
    - batch processing : 128 batch (32 pos, 96 neg)
'''
import time
import copy
import os
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torchvision.transforms as transforms
from torchvision.models import alexnet

from utils.data.custom_classifier_dataset import CustomClassifierDataset
from utils.data.custom_hard_negative_mining_dataset import CustomHardNegativeMiningDataset
from utils.data.custom_batch_sampler import CustomBatchSampler
from utils.util import check_dir
from utils.util import save_model

batch_positive = 32
batch_negative = 96
batch_total = 128


def load_data(data_root_dir):
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((227, 227)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    data_loaders = {}
    data_sizes = {}
    remain_negative_list = list()
    for name in ['train', 'val']:
        # ./data/classifier_car/{name}
        data_dir = os.path.join(data_root_dir, name)

        data_set = CustomClassifierDataset(data_dir, transform=transform)
        if name is 'train':
            """
            positive 데이터가 negative 데이터보다 훨씬 적으므로 1:1 비율로 dataset을 만들기 위해서
            positive 데이터 개수만큼 negative 데이터를 랜덤으로 뽑는다.
            """
            positive_list = data_set.get_positives()
            negative_list = data_set.get_negatives()

            # negative sample들 중에서 positive sample 개수만큼 랜덤으로 뽑는다.
            init_negative_idxs = random.sample(range(len(negative_list)), len(positive_list))
            # 뽑은 neg 리스트
            init_negative_list = [negative_list[idx] for idx in range(len(negative_list)) if idx in init_negative_idxs]
            # 남은 neg 리스트
            remain_negative_list = [negative_list[idx] for idx in range(len(negative_list))
                                    if idx not in init_negative_idxs]

            data_set.set_negative_list(init_negative_list)
            data_loaders['remain'] = remain_negative_list
    
        # 그렇게 1:1로 맞춘 dataset에서 (32 pos, 96 neg) 비율로 샘플링
        sampler = CustomBatchSampler(data_set.get_positive_num(), data_set.get_negative_num(),
                                     batch_positive, batch_negative)

        data_loader = DataLoader(data_set, batch_size=batch_total, sampler=sampler, num_workers=8, drop_last=True)
        data_loaders[name] = data_loader
        data_sizes[name] = len(sampler)
    return data_loaders, data_sizes


def hinge_loss(outputs, labels):
    """
    :param outputs: (N, num_classes)
    :param labels: (N)
    :return: loss
    """
    num_labels = len(labels)
    corrects = outputs[range(num_labels), labels].unsqueeze(0).T

    margin = 1.0
    margins = outputs - corrects + margin
    loss = torch.sum(torch.max(margins, 1)[0]) / len(labels)

    # # 正则化强度
    # reg = 1e-3
    # loss += reg * torch.sum(weight ** 2)

    return loss


def add_hard_negatives(hard_negative_list, negative_list, add_negative_list):
    for item in hard_negative_list:
        if len(add_negative_list) == 0:
            # 첫 neg 샘플 추가
            negative_list.append(item)
            add_negative_list.append(list(item['rect']))
        if list(item['rect']) not in add_negative_list:
            negative_list.append(item)
            add_negative_list.append(list(item['rect']))


def get_hard_negatives(preds, cache_dicts):
    '''
    # false positive(객체라고 예측하지만 배경인 경우) : 어려운 샘플
    # true negative(배경이라고 예측한 것이 맞은 경우) : 쉬운 샘플
    '''
    # false positive(객체라고 예측하지만 배경인 경우) : 어려운 샘플
    fp_mask = preds == 1
    # true negative(배경이라고 예측한 것이 맞은 경우) : 쉬운 샘플
    tn_mask = preds == 0

    fp_rects = cache_dicts['rect'][fp_mask].numpy()
    fp_image_ids = cache_dicts['image_id'][fp_mask].numpy()

    tn_rects = cache_dicts['rect'][tn_mask].numpy()
    tn_image_ids = cache_dicts['image_id'][tn_mask].numpy()

    hard_negative_list = [{'rect': fp_rects[idx], 'image_id': fp_image_ids[idx]} for idx in range(len(fp_rects))]
    easy_negatie_list = [{'rect': tn_rects[idx], 'image_id': tn_image_ids[idx]} for idx in range(len(tn_rects))]

    return hard_negative_list, easy_negatie_list


def train_model(data_loaders,
                model,
                criterion,
                optimizer,
                lr_scheduler,
                num_epochs=25,
                device=None):
    
    since = time.time()

    best_model_weights = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):

        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)

        # Each epoch has a training and validation phase
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()  # Set model to training mode
            else:
                model.eval()  # Set model to evaluate mode

            running_loss = 0.0
            running_corrects = 0

            # pos/neg 개수
            data_set = data_loaders[phase].dataset
            print('{} - positive_num: {} - negative_num: {} - data size: {}'.format(
                phase, data_set.get_positive_num(), data_set.get_negative_num(), data_sizes[phase]))

            # Iterate over data.
            for inputs, labels, cache_dicts in data_loaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward
                # track history if only in train
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    # print(outputs.shape)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    # backward + optimize only if in training phase
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                # statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
            if phase == 'train':
                lr_scheduler.step()

            epoch_loss = running_loss / data_sizes[phase]
            epoch_acc = running_corrects.double() / data_sizes[phase]

            print('{} Loss: {:.4f} Acc: {:.4f}'.format(
                phase, epoch_loss, epoch_acc))

            # deep copy the model
            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_weights = copy.deepcopy(model.state_dict())

        # 매 iter 마무리마다 뽑고 남은 remain_negative sample들로 test
        train_dataset = data_loaders['train'].dataset
        remain_negative_list = data_loaders['remain']
        jpeg_images = train_dataset.get_jpeg_images()
        transform = train_dataset.get_transform()

        with torch.set_grad_enabled(False):
            # 남아있는 neg 샘플로 negative mining 데이터셋을 만든다.
            remain_dataset = CustomHardNegativeMiningDataset(remain_negative_list, jpeg_images, transform=transform)
            remain_data_loader = DataLoader(remain_dataset, batch_size=batch_total, num_workers=8, drop_last=True)

            # remain_negative dataset
            negative_list = train_dataset.get_negatives()
            # {'add_negative':[]}
            add_negative_list = data_loaders.get('add_negative', [])

            running_corrects = 0
            # Iterate over data.
            for inputs, labels, cache_dicts in remain_data_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)

                # zero the parameter gradients
                optimizer.zero_grad()

                outputs = model(inputs)
                # print(outputs.shape)
                _, preds = torch.max(outputs, 1)

                running_corrects += torch.sum(preds == labels.data)

                # hard_negative : FP, easy_negative : TN
                hard_negative_list, easy_neagtive_list = get_hard_negatives(preds.cpu().numpy(), cache_dicts)
                add_hard_negatives(hard_negative_list, negative_list, add_negative_list)

            remain_acc = running_corrects.double() / len(remain_negative_list)
            print('remiam negative size: {}, acc: {:.4f}'.format(len(remain_negative_list), remain_acc))

            # 학습 종료 후 네거티브 샘플을 리셋하고 
            train_dataset.set_negative_list(negative_list)
            tmp_sampler = CustomBatchSampler(train_dataset.get_positive_num(), train_dataset.get_negative_num(),
                                             batch_positive, batch_negative)
            data_loaders['train'] = DataLoader(train_dataset, batch_size=batch_total, sampler=tmp_sampler,
                                               num_workers=8, drop_last=True)
            data_loaders['add_negative'] = add_negative_list
            # 데이터 세트 크기 초기화
            data_sizes['train'] = len(tmp_sampler)

        # 매 훈련마다 저장
        save_model(model, 'models/linear_svm_alexnet_car_%d.pth' % epoch)

    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(
        time_elapsed // 60, time_elapsed % 60))
    print('Best val Acc: {:4f}'.format(best_acc))

    # load best model weights
    model.load_state_dict(best_model_weights)
    return model


if __name__ == '__main__':
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    data_loaders, data_sizes = load_data('./data/classifier_car')

    # fine-tuned alexnet 불러오기
    model_path = './models/alexnet_car.pth'
    model = alexnet()
    num_classes = 2
    num_features = model.classifier[6].in_features
    model.classifier[6] = nn.Linear(num_features, num_classes)
    model.load_state_dict(torch.load(model_path))
    model.eval()
    
    # 변수 고정
    for param in model.parameters():
        param.requires_grad = False
    # SVM 분류기 생성 - classifier 마지막 부분만 가중치를 초기화
    model.classifier[6] = nn.Linear(num_features, num_classes)
    model = model.to(device)

    # loss 함수 설정
    criterion = hinge_loss
    optimizer = optim.SGD(model.parameters(), lr=1e-4, momentum=0.9)
    # iter: 10, 4iter마다 학습률 감소
    lr_schduler = optim.lr_scheduler.StepLR(optimizer, step_size=4, gamma=0.1)

    best_model = train_model(
        data_loaders,
        model,
        criterion,
        optimizer,
        lr_schduler,
        num_epochs=10,
        device=device
    )
    save_model(best_model, 'models/best_linear_svm_alexnet_car.pth')
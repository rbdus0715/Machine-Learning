# 1. 붓꽃 품종 예측
import sklearn
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
iport pandas as pd
iris = load_iris()
iris_data = iris.data
iris_label = iris.target
df = pd.DataFrame(data=iris_data, columns=iris.feature_names)
df['label'] = iris_label
X_train, X_test, y_train, y_test = train_test_split(iris_data, iris_label, test_size=0.2, random_state=11)
dt_clf = DecisionTreeClassifier(random_state=11)
dt_clf.fit(X_train, y_train)
pred = dt_clf.predict(X_test)
from sklearn.metrics import accuracy_score
accuracy_score(y_test, pred)


# 2. 교차검증 간편하게 하기 -> cross_val_score
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import cross_val_score, cross_validate
iris = load_iris()
features = iris.data
label = iris.target
dt_clf = DecisionTreeClassifier(random_state=156)
scores = cross_val_score(dt_clf, features, label, scoring='accuracy', cv=3)
print(np.round(np.mean(scores), 4))


# 3. 그리드서치CV 교차검증 + 하이퍼 파라미터 튜닝
from sklearn.model_selection import train_test_split, GridSearchCV
import pandas as pd
iris_data = load_iris()
X_train, X_test, y_train, y_test = train_test_split(iris_data.data, iris_data.target, test_size=0.2, random_state=121)
dtree = DecisionTreeClassifier()
parameters = {
    'max_depth' : [1, 2, 3],
    'min_samples_split' : [2, 3]
}
grid_dtree = GridSearchCV(dtree, param_grid=parameters, cv=3, refit=True)
grid_dtree.fit(X_train, y_train)
scores_df = pd.DataFrame(grid_dtree.cv_results_) # 결과확인
print(grid_dtree.best_params_) # 최고 파라미터 조합
print(grid_dtree.best_score_) # 최고 점수
estimator = grid_dtree.best_estimator_ # 최종 모델
pred = estimator.predict(X_test) # 최종 모델로 예측
print(accuracy_score(y_test, pred))


# 4. 데이터 인코딩
## 레이블 인코딩
items = ['a', 'b', 'c']
from sklearn.preprocessing import LabelEncoder
encoder = LabelEncoder()
encoder.fit(items)
labels = encoder.transform(items)
print(encoder.classes_, labels,encoder.inverse_transform([0, 1, 2]))
## 원핫 인코딩
from sklearn.preprocessing import OneHotEncoder
encoder = LabelEncoder()
encoder.fit(items)
labels = encoder.transform(items)
labels = labels.reshape(-1 ,1) # 2차원 데이터로 변환
oh_encoder = OneHotEncoder()
oh_encoder.fit(labels)
oh_labels = oh_encoder.transform(labels)
print(oh_labels.toarray())
## 원핫 인코딩 쉽게하기
import pandasas pd
df =pd.DataFrame({'items':['a', 'b', 'c'])
pd.get_dummies(df)
## 피처 스케일링과 정규화
### - 표준화 : 평균이 0이고 분산이 1일 분포로 변환
from sklearn.datasets import load_iris
import pandas as pd
iris = load_iris()
iris_data = iris.data
iris_df =pd.DataFrame(data=iris_data, columns=iris.feature_names)
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(iris_df)
iris_scaled = scaler.transform(iris_df)
iris_df_sclaed = pd.DataFrame(data=iris_scaled, columns=iris.feature_names)
### - 정규화 : 데이터를 일정 범위내의 수치로 변환
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
scaler.fit(iris_df)
iris_scaled = scaler.transform(iris_df)
iris_df_scaled = pd.DataFrame(data=iris_scaled, columns=iris.feature_names)

## 데이터 탐색
- 분류 문제에서 결과 비율이 어떻게 된는지 : df[결과].value_counts()
- null 값 확인하기 data.info()


## 평가
- 이진분류 문제에서 평가 : [evaluation.get_clf_eval](https://github.com/rbdus0715/Machine-Learning/blob/main/team-note/evaluation.py)


## 피드백
- 데이터 탐색에서 본 결과 비율에 따라 정밀도, 재현율 어느 것에 초점을 맞출 것인지 >> 임계값 조절
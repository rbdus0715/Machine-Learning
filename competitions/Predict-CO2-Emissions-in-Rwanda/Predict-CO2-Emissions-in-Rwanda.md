# CO2 배출량 예측하기

## 데이터 분석 단계


**(1) 통계 요약을 통해서 데이터에 대한 전체적인 감을 잡는다. 이때 최대 최소에 대한 정보를 정리해두기!**
```python
# 통계 요약 statistical summaries 할때 더 자세한 정보를 얻을 수 있음
df.describe(include='all')
```


**(2) 타겟 데이터의 분포와 왜도 확인: sns.histplot**
- 왜도(skewness): 데이터 분포의 비대칭성을 나타내는 지표
  - 0에 가까움: 대칭 | 양수: 왼쪽으로 치우침 | 음수: 오른쪽으로 치우침

![imag](https://www.gstatic.com/education/formulas2/553212783/en/skewness.svg) 
- $x_i$: 데이터 포인트
- $\bar{x}$: 평균
- $\sigmaσ$: 데이터의 표준편차
- $n$: 데이터 포인트의 수
​- 해결방법
```python
# 타깃값의 분포 확인하기 
sns.set_style('darkgrid') # 다양한 옵션 : darkgrid, whitegrid, dark, white, ticks
plt.figure(figsize=(13, 7))
sns.histplot(train.emission, kde = True, bins = 15) # bins : 막대의 개수
plt.title('타겟 분포', y=1.02, fontsize=15)
display(plt.show(), train.emission.skew()) # display 함수는 대화형 환경에서의 출력함수
```
- 왜도 현상 해결법
  - 로그변환, box-cox 변환, 루트변환


 **(3) 이상치 확인하기 [공부했던 링크](https://github.com/rbdus0715/Machine-Learning/blob/main/study/sklearn/creditcard_fraud.ipynb)**
![imag](https://www.simplypsychology.org/wp-content/uploads/box-whisker-plot.jpg)
- 그래프 해석
  - 상자: 데이터의 사분위수 범위 Q1~Q3
  - 수염: 이상치의 경계, 보통 1.5배 사분위범위를 사용하여 길이를 정함
  - 이상치: 수염의 범위를 벗어나느 값
  - 상자의 위치에 따라서 데이터의 분포도도 파악 가능
```python
sns.set_style('dark')
plt.figure(figsize=(13,7))
sns.boxplot(train.emission)
plt.title('target data outliers check', y=1.02, fontsize=15)
plt.show()
```

**(4) 데이터에 위도와 경도 수치가 주어진 상황, 지리 정보 시각화 (geopandas)**
- [geopandas with folium 사용설명서](https://geopandas.org/en/stable/gallery/plotting_with_folium.html)

**(5) 피처 데이터 개수 확인**
- 개수 분포를 알고싶은 피처: col1
```python
plt.figure(figsize=(14, 7))
sns.countplot(x='col1', data=df)
```

**(6) 타겟 데이터와 가장 상관관계가 큰 피처 Top 20 시각화**
```python
# 타겟 데이터와 가장 상관관계가 큰 피처 Top 20
def top_20_corr(df, target_name):
    top20_corrs = abs(df.corr()[target_name]).sort_values(ascending=False).head(20)
    corr = train[list(top20_corrs.index)].corr()
    plt.figure(figsize=(13, 8))
    sns.heatmap(corr, cmap='RdBu', annot=True)

# 예시 사용
top_20_corr(train, 'emission')
```

## 모델링 단계
**(1) 시드값 설정**
```python
SEED = 2023
random.seed(SEED)
np.random.seed(SEED)
```

## 추가적으로 도움될만한 것들
**(1) 군집화**
- [k-mean 군집화](https://github.com/rbdus0715/Machine-Learning/blob/main/competitions/Predict-CO2-Emissions-in-Rwanda/%EA%B5%B0%EC%A7%91%ED%99%94%EB%A1%9C_%EC%97%85%EA%B7%B8%EB%A0%88%EC%9D%B4%EB%93%9C.ipynb)

**(2) haversine : 둥근 지구에서 직선거리를 평면으로 계산**
- pip install haversine
```python
from haversine import haversine
Seoul = (37.541, 126.986)
Toronto = (43.65, -79.38)
haversine(Seoul, Toronto, unit='km') # 거리 계산
```



## 새롭게 알게된 정보
**(1) python으로 날짜 다룰 때**
- strftime : 날짜와 시간을 문자열로 출력
```python
import datetime
datetime = now.strftime('%Y-%m-%d %H:%M:%S')
print(datetime)  # 2021-04-08 21:28:20
```
- strptime : 날짜와 시간 형식의 문자열을 datetime으로 변환
```python
str_datetime = '2021-04-08 21:31:48'
currdate = datetime.datetime.strptime(str_datetime, '%Y-%m-%d %H:%M:%S')
print(type(currdate)) 	# [class 'datetime.datetime']
```

**(2) 결측치 새로운 값으로 대체할 때**
- df.ffill() : null값을 새로운 값으로 대체할 때 바로 앞의 데이터를 참조 = df.fillna(method='ffill')
- df.bfill() : 바로 뒤의 데이터를 참조 = df.fillna(method='bfill')
- 앞의 두 함수를 묶어서 한 번에 df.ffill().bfill()로 사용하기도 함
- [자세한 설명](https://songseungwon.tistory.com/81)

**(3) f-String**
- f-string 만드는 법 : 문자열 앞에 f 또는 F 붙여주기
- 여러 기능
  - 변수 치환 : f"{x} + {y}는 {x+y}입니다."
  - 함수 호출 : f"{word}는 {len(word)}글자 입니다."
  - 표현식, 객체 등등...
- [자세한 설명](https://www.daleseo.com/python-f-strings/)

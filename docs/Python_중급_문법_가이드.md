# Python 중급 문법 완벽 가이드
## 고등학생을 위한 단계별 학습

---

## 📋 목차

1. [출력문과 입력 (Print & Input)](#1-출력문과-입력-print--input)
2. [반복문 (Loops)](#2-반복문-loops)
3. [Random 함수](#3-random-함수)
4. [함수 (Functions)](#4-함수-functions)
5. [모듈과 패키지 (Modules & Packages)](#5-모듈과-패키지-modules--packages)
6. [클래스 (Classes)](#6-클래스-classes)
7. [리스트 (List)](#7-리스트-list)
8. [딕셔너리 (Dictionary)](#8-딕셔너리-dictionary)
9. [람다 함수 (Lambda)](#9-람다-함수-lambda)
10. [Map, Filter, Reduce](#10-map-filter-reduce)
11. [컴프리헨션 (Comprehension)](#11-컴프리헨션-comprehension)
12. [예외 처리 (Exception Handling)](#12-예외-처리-exception-handling)
13. [파일 입출력 (File I/O)](#13-파일-입출력-file-io)

---

## 1. 출력문과 입력 (Print & Input)

### 📌 개념 이해

**출력(Print)이란?**
- 화면에 데이터를 표시하는 기능
- `print()` 함수 사용
- 프로그램 결과 확인 및 디버깅에 필수

**입력(Input)이란?**
- 사용자로부터 데이터를 받는 기능
- `input()` 함수 사용
- 대화형 프로그램 제작에 필요

### 💡 기본 출력 (Print)

```python
# 예시 1: 기본 출력
print("Hello, World!")  # 출력: Hello, World!

# 예시 2: 여러 값 출력
print("Python", "is", "fun")  # 출력: Python is fun

# 예시 3: 변수 출력
name = "Alice"
age = 17
print("Name:", name, "Age:", age)  # 출력: Name: Alice Age: 17

# 예시 4: 숫자 계산 출력
result = 10 + 20
print("Result:", result)  # 출력: Result: 30
```

### 📊 Print 함수 매개변수

| 매개변수 | 설명 | 기본값 | 예시 |
|---------|------|--------|------|
| `sep` | 구분자 설정 | 공백 `' '` | `print(1, 2, 3, sep='-')` → `1-2-3` |
| `end` | 끝 문자 설정 | 줄바꿈 `'\n'` | `print("Hi", end='!')` → `Hi!` |
| `file` | 출력 위치 | 화면 | 파일로 출력 가능 |
| `flush` | 버퍼 비우기 | False | 즉시 출력 |

```python
# 1. sep 사용 (구분자 변경)
print("Apple", "Banana", "Cherry", sep=", ")
# 출력: Apple, Banana, Cherry

# 2. end 사용 (줄바꿈 제거)
print("Loading", end="...")
print("Done!")
# 출력: Loading...Done!

# 3. 반복문에서 같은 줄 출력
for i in range(5):
    print(i, end=" ")
print()  # 줄바꿈
# 출력: 0 1 2 3 4

# 4. 여러 구분자 조합
print("2024", "12", "17", sep="-")
# 출력: 2024-12-17
```

### 🎨 포맷팅 (Formatting)

```python
name = "Bob"
age = 18
score = 95.5

# 방법 1: f-string (Python 3.6+) - 권장
print(f"Name: {name}, Age: {age}, Score: {score}")
# 출력: Name: Bob, Age: 18, Score: 95.5

# 방법 2: format() 메서드
print("Name: {}, Age: {}, Score: {}".format(name, age, score))
# 출력: Name: Bob, Age: 18, Score: 95.5

# 방법 3: % 연산자 (오래된 방식)
print("Name: %s, Age: %d, Score: %.1f" % (name, age, score))
# 출력: Name: Bob, Age: 18, Score: 95.5
```

**f-string 고급 사용법**

```python
# 1. 표현식 사용
x = 10
y = 20
print(f"{x} + {y} = {x + y}")
# 출력: 10 + 20 = 30

# 2. 소수점 자릿수 지정
pi = 3.141592
print(f"Pi: {pi:.2f}")  # 소수점 2자리
# 출력: Pi: 3.14

# 3. 정렬
name = "Alice"
print(f"|{name:>10}|")  # 오른쪽 정렬 (10칸)
print(f"|{name:<10}|")  # 왼쪽 정렬 (10칸)
print(f"|{name:^10}|")  # 가운데 정렬 (10칸)
# 출력:
# |     Alice|
# |Alice     |
# |  Alice   |

# 4. 숫자 천 단위 구분
number = 1234567
print(f"{number:,}")
# 출력: 1,234,567
```

### 📥 기본 입력 (Input)

```python
# 예시 1: 문자열 입력
name = input("Enter your name: ")
print(f"Hello, {name}!")

# 예시 2: 숫자 입력 (형변환 필요)
age = int(input("Enter your age: "))
print(f"You are {age} years old")

# 예시 3: 실수 입력
height = float(input("Enter your height (cm): "))
print(f"Your height is {height}cm")

# 예시 4: 여러 값 입력
numbers = input("Enter three numbers (space separated): ")
num1, num2, num3 = numbers.split()
print(f"Numbers: {num1}, {num2}, {num3}")
```

### 🎯 실용적인 예시

```python
# 간단한 계산기
print("=== Simple Calculator ===")
num1 = float(input("Enter first number: "))
num2 = float(input("Enter second number: "))

print(f"\nResults:")
print(f"{num1} + {num2} = {num1 + num2}")
print(f"{num1} - {num2} = {num1 - num2}")
print(f"{num1} * {num2} = {num1 * num2}")
if num2 != 0:
    print(f"{num1} / {num2} = {num1 / num2:.2f}")

# 실행 예시:
# === Simple Calculator ===
# Enter first number: 10
# Enter second number: 3
# 
# Results:
# 10.0 + 3.0 = 13.0
# 10.0 - 3.0 = 7.0
# 10.0 * 3.0 = 30.0
# 10.0 / 3.0 = 3.33
```

---

## 2. 반복문 (Loops)

### 📌 개념 이해

**반복문이란?**
- 같은 코드를 여러 번 실행
- `for`문과 `while`문 제공
- 효율적인 프로그래밍의 핵심

### 🔄 For 반복문

**기본 구조**

```python
for variable in iterable:
    # 반복할 코드
    pass
```

```python
# 예시 1: 리스트 반복
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)
# 출력:
# apple
# banana
# cherry

# 예시 2: 문자열 반복
word = "Python"
for char in word:
    print(char, end=" ")
print()
# 출력: P y t h o n

# 예시 3: 딕셔너리 반복
student = {"name": "Alice", "age": 17, "grade": 11}
for key, value in student.items():
    print(f"{key}: {value}")
# 출력:
# name: Alice
# age: 17
# grade: 11
```

### 📊 Range 함수

**range() 구조**

```python
range(stop)           # 0부터 stop-1까지
range(start, stop)    # start부터 stop-1까지
range(start, stop, step)  # start부터 stop-1까지 step씩 증가
```

| 사용법 | 설명 | 예시 | 결과 |
|--------|------|------|------|
| `range(5)` | 0~4 | `list(range(5))` | `[0, 1, 2, 3, 4]` |
| `range(2, 7)` | 2~6 | `list(range(2, 7))` | `[2, 3, 4, 5, 6]` |
| `range(1, 10, 2)` | 1~9, 2씩 증가 | `list(range(1, 10, 2))` | `[1, 3, 5, 7, 9]` |
| `range(10, 0, -1)` | 10~1, 감소 | `list(range(10, 0, -1))` | `[10, 9, ..., 1]` |

```python
# 예시 1: 숫자 반복
for i in range(5):
    print(i, end=" ")
print()
# 출력: 0 1 2 3 4

# 예시 2: 시작과 끝 지정
for i in range(1, 6):
    print(i, end=" ")
print()
# 출력: 1 2 3 4 5

# 예시 3: 증가값 지정
for i in range(0, 11, 2):
    print(i, end=" ")
print()
# 출력: 0 2 4 6 8 10

# 예시 4: 역순 반복
for i in range(5, 0, -1):
    print(i, end=" ")
print()
# 출력: 5 4 3 2 1
```

### 🔁 While 반복문

**기본 구조**

```python
while condition:
    # 조건이 True일 때 실행
    pass
```

```python
# 예시 1: 기본 while 문
count = 0
while count < 5:
    print(count, end=" ")
    count += 1
print()
# 출력: 0 1 2 3 4

# 예시 2: 사용자 입력 받기
password = ""
while password != "1234":
    password = input("Enter password: ")
    if password != "1234":
        print("Wrong password. Try again.")
print("Access granted!")

# 예시 3: 무한 루프 (조심!)
# while True:
#     print("This will run forever!")
#     break  # break로 탈출
```

### 🎛️ Break와 Continue

```python
# 1. break - 반복문 즉시 종료
print("Break example:")
for i in range(10):
    if i == 5:
        break
    print(i, end=" ")
print()
# 출력: 0 1 2 3 4

# 2. continue - 현재 반복만 건너뛰기
print("\nContinue example:")
for i in range(10):
    if i % 2 == 0:
        continue
    print(i, end=" ")
print()
# 출력: 1 3 5 7 9

# 3. break와 continue 조합
print("\nCombined example:")
for i in range(1, 11):
    if i % 2 == 0:
        continue  # 짝수 건너뛰기
    if i > 7:
        break  # 7 초과하면 종료
    print(i, end=" ")
print()
# 출력: 1 3 5 7
```

### 📊 Enumerate와 Zip

```python
# 1. enumerate - 인덱스와 값 동시 접근
fruits = ["apple", "banana", "cherry"]

print("Enumerate example:")
for index, fruit in enumerate(fruits):
    print(f"{index}: {fruit}")
# 출력:
# 0: apple
# 1: banana
# 2: cherry

# 시작 인덱스 지정
for index, fruit in enumerate(fruits, start=1):
    print(f"{index}. {fruit}")
# 출력:
# 1. apple
# 2. banana
# 3. cherry


# 2. zip - 여러 리스트 동시 반복
names = ["Alice", "Bob", "Charlie"]
scores = [85, 92, 78]

print("\nZip example:")
for name, score in zip(names, scores):
    print(f"{name}: {score}")
# 출력:
# Alice: 85
# Bob: 92
# Charlie: 78
```

### 🔄 중첩 반복문

```python
# 예시 1: 구구단
print("=== Multiplication Table ===")
for i in range(2, 6):
    print(f"\n{i}단:")
    for j in range(1, 10):
        print(f"{i} x {j} = {i*j}")

# 예시 2: 별 패턴
print("\n=== Star Pattern ===")
for i in range(1, 6):
    for j in range(i):
        print("*", end="")
    print()
# 출력:
# *
# **
# ***
# ****
# *****

# 예시 3: 2차원 리스트 순회
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]

print("\n=== Matrix ===")
for row in matrix:
    for element in row:
        print(element, end=" ")
    print()
# 출력:
# 1 2 3 
# 4 5 6 
# 7 8 9
```

### 🎯 실용적인 예시

```python
# 학생 점수 처리
students = [
    {"name": "Alice", "score": 85},
    {"name": "Bob", "score": 92},
    {"name": "Charlie", "score": 78},
    {"name": "David", "score": 95}
]

print("=== Student Scores ===")
total_score = 0
pass_count = 0

for index, student in enumerate(students, 1):
    name = student["name"]
    score = student["score"]
    
    # 등급 계산
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    else:
        grade = "C"
    
    # 합격 여부
    status = "Pass" if score >= 80 else "Fail"
    if score >= 80:
        pass_count += 1
    
    total_score += score
    print(f"{index}. {name}: {score}점 (등급: {grade}, {status})")

# 통계
average = total_score / len(students)
print(f"\n--- Statistics ---")
print(f"Average Score: {average:.2f}")
print(f"Pass Rate: {pass_count}/{len(students)}")
```

---

## 3. Random 함수

### 📌 개념 이해

**Random이란?**
- 난수(무작위 수)를 생성하는 모듈
- 게임, 시뮬레이션, 테스트에 필수
- `import random` 으로 사용

### 📊 주요 Random 함수

| 함수 | 설명 | 예시 | 결과 범위 |
|------|------|------|----------|
| `random()` | 0~1 사이 실수 | `random.random()` | `0.0 ≤ x < 1.0` |
| `randint(a, b)` | a~b 사이 정수 | `random.randint(1, 10)` | `1 ≤ x ≤ 10` |
| `uniform(a, b)` | a~b 사이 실수 | `random.uniform(1.0, 10.0)` | `1.0 ≤ x ≤ 10.0` |
| `choice(seq)` | 시퀀스에서 랜덤 선택 | `random.choice([1,2,3])` | 하나의 요소 |
| `shuffle(list)` | 리스트 섞기 | `random.shuffle(my_list)` | 원본 변경 |
| `sample(seq, k)` | k개 랜덤 선택 | `random.sample([1,2,3,4], 2)` | 중복 없이 |

### 💡 기본 예시

```python
import random

# 예시 1: random() - 0~1 사이 실수
print("random():", random.random())
# 출력: random(): 0.7234912847329847 (매번 다름)

# 예시 2: randint() - 정수 범위
dice = random.randint(1, 6)
print(f"Dice roll: {dice}")
# 출력: Dice roll: 4 (1~6 중 하나)

# 예시 3: uniform() - 실수 범위
temperature = random.uniform(15.0, 30.0)
print(f"Temperature: {temperature:.1f}°C")
# 출력: Temperature: 23.7°C

# 예시 4: choice() - 리스트에서 선택
colors = ["red", "blue", "green", "yellow"]
selected_color = random.choice(colors)
print(f"Selected color: {selected_color}")
# 출력: Selected color: blue
```

### 🎲 랜덤 정수 생성

```python
import random

# 1. randint() - 양 끝 포함
for i in range(5):
    print(random.randint(1, 10), end=" ")
print()
# 출력: 3 7 1 9 5

# 2. randrange() - 끝 미포함
for i in range(5):
    print(random.randrange(1, 11), end=" ")  # 1~10
print()
# 출력: 2 8 4 10 6

# 3. randrange() with step
even_number = random.randrange(0, 11, 2)  # 0, 2, 4, 6, 8, 10 중 선택
print(f"Random even number: {even_number}")
```

### 🎯 Choice, Choices, Sample

```python
import random

fruits = ["apple", "banana", "cherry", "grape", "orange"]

# 1. choice() - 하나 선택
fruit1 = random.choice(fruits)
print(f"Choice: {fruit1}")
# 출력: Choice: banana

# 2. choices() - 중복 허용, 여러 개 선택
fruit2 = random.choices(fruits, k=3)
print(f"Choices (duplicate allowed): {fruit2}")
# 출력: Choices (duplicate allowed): ['apple', 'apple', 'cherry']

# 3. sample() - 중복 없이 여러 개 선택
fruit3 = random.sample(fruits, k=3)
print(f"Sample (no duplicate): {fruit3}")
# 출력: Sample (no duplicate): ['cherry', 'orange', 'apple']

# 4. choices() with weights (가중치)
weighted_fruits = random.choices(
    fruits, 
    weights=[5, 1, 1, 1, 1],  # apple이 선택될 확률이 높음
    k=10
)
print(f"Weighted choices: {weighted_fruits}")
# 출력: Weighted choices: ['apple', 'banana', 'apple', 'apple', ...]
```

### 🔀 Shuffle - 리스트 섞기

```python
import random

# 예시 1: 카드 덱 섞기
cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
print(f"Original: {cards[:5]}...")

random.shuffle(cards)
print(f"Shuffled: {cards[:5]}...")
# 출력:
# Original: ['A', '2', '3', '4', '5']...
# Shuffled: ['7', 'K', '3', 'A', '9']...

# 예시 2: 학생 순서 무작위 배정
students = ["Alice", "Bob", "Charlie", "David", "Eve"]
print(f"\nOriginal order: {students}")

random.shuffle(students)
print(f"Random order: {students}")
# 출력:
# Original order: ['Alice', 'Bob', 'Charlie', 'David', 'Eve']
# Random order: ['Charlie', 'Eve', 'Alice', 'David', 'Bob']
```

### 🎲 실수 난수 생성

```python
import random

# 1. random() - 0.0~1.0
probability = random.random()
print(f"Probability: {probability:.4f}")
# 출력: Probability: 0.7384

# 2. uniform() - 범위 지정
price = random.uniform(10.0, 100.0)
print(f"Random price: ${price:.2f}")
# 출력: Random price: $45.67

# 3. gauss() - 정규분포 (평균, 표준편차)
height = random.gauss(170, 10)  # 평균 170cm, 표준편차 10
print(f"Random height: {height:.1f}cm")
# 출력: Random height: 165.3cm
```

### 🌱 Seed - 재현 가능한 난수

```python
import random

# seed 설정 - 같은 시드는 같은 난수 생성
random.seed(42)
print("First run:")
for i in range(5):
    print(random.randint(1, 100), end=" ")
print()

# 같은 seed 다시 설정
random.seed(42)
print("Second run (same seed):")
for i in range(5):
    print(random.randint(1, 100), end=" ")
print()

# 출력:
# First run:
# 82 15 87 57 98
# Second run (same seed):
# 82 15 87 57 98  (완전히 동일!)
```

### 🎯 실용적인 예시

```python
import random

# 1. 주사위 게임
print("=== Dice Game ===")
player1 = random.randint(1, 6)
player2 = random.randint(1, 6)

print(f"Player 1 rolled: {player1}")
print(f"Player 2 rolled: {player2}")

if player1 > player2:
    print("Player 1 wins!")
elif player2 > player1:
    print("Player 2 wins!")
else:
    print("It's a tie!")


# 2. 랜덤 비밀번호 생성기
print("\n=== Password Generator ===")
characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%"
password_length = 12

password = ''.join(random.choice(characters) for _ in range(password_length))
print(f"Generated password: {password}")
# 출력: Generated password: aB3$mK9!xPz2


# 3. 로또 번호 생성기
print("\n=== Lotto Number Generator ===")
lotto_numbers = random.sample(range(1, 46), 6)  # 1~45 중 6개
lotto_numbers.sort()
print(f"Your lotto numbers: {lotto_numbers}")
# 출력: Your lotto numbers: [7, 15, 23, 31, 38, 42]


# 4. 퀴즈 문제 무작위 출제
print("\n=== Random Quiz ===")
questions = [
    {"q": "What is 2+2?", "a": "4"},
    {"q": "What is 3*3?", "a": "9"},
    {"q": "What is 10-5?", "a": "5"},
    {"q": "What is 8/2?", "a": "4"}
]

random_questions = random.sample(questions, 2)
for i, question in enumerate(random_questions, 1):
    print(f"{i}. {question['q']}")
    answer = input("Your answer: ")
    if answer == question['a']:
        print("Correct!")
    else:
        print(f"Wrong! The answer is {question['a']}")


# 5. 확률 기반 이벤트
print("\n=== Lucky Draw ===")
chance = random.random()

if chance < 0.01:  # 1% 확률
    print("Jackpot! You won $1000!")
elif chance < 0.10:  # 9% 확률
    print("Great! You won $100!")
elif chance < 0.30:  # 20% 확률
    print("Nice! You won $10!")
else:  # 70% 확률
    print("Better luck next time!")
```

### 🎮 게임 예제: 숫자 맞추기

```python
import random

print("=== Number Guessing Game ===")
print("I'm thinking of a number between 1 and 100")

target = random.randint(1, 100)
attempts = 0
max_attempts = 7

while attempts < max_attempts:
    attempts += 1
    remaining = max_attempts - attempts + 1
    
    guess = int(input(f"\nAttempt {attempts}/{max_attempts} - Enter your guess: "))
    
    if guess == target:
        print(f"🎉 Congratulations! You found it in {attempts} attempts!")
        break
    elif guess < target:
        print(f"Too low! {remaining} attempts remaining")
    else:
        print(f"Too high! {remaining} attempts remaining")
else:
    print(f"\n😢 Game Over! The number was {target}")
```

---

## 4. 함수 (Functions)

### 📌 개념 이해

**함수란?**
- 특정 작업을 수행하는 코드 블록
- 재사용 가능한 코드 조각
- 입력(매개변수)을 받아 출력(반환값)을 생성

**왜 함수를 사용할까?**
- 코드 재사용성 향상
- 코드 가독성 증가
- 유지보수 용이

### 🔍 함수의 구조

```python
def function_name(parameter1, parameter2):
    """
    함수 설명 (Docstring)
    """
    # 함수 본문
    result = parameter1 + parameter2
    return result
```

### 📊 함수 구성 요소

| 구성 요소 | 설명 | 필수 여부 |
|----------|------|----------|
| `def` | 함수 정의 키워드 | 필수 |
| `function_name` | 함수 이름 | 필수 |
| `parameters` | 입력 매개변수 | 선택 |
| `docstring` | 함수 설명 | 선택 (권장) |
| `return` | 반환값 | 선택 |

### 💡 기본 예시

```python
# 예시 1: 기본 함수
def greet():
    """인사를 출력하는 함수"""
    print("Hello, World!")

greet()  # 출력: Hello, World!


# 예시 2: 매개변수가 있는 함수
def greet_person(name):
    """이름을 받아 인사하는 함수"""
    print(f"Hello, {name}!")

greet_person("Alice")  # 출력: Hello, Alice!


# 예시 3: 반환값이 있는 함수
def add_numbers(a, b):
    """두 숫자를 더한 결과를 반환"""
    result = a + b
    return result

sum_result = add_numbers(5, 3)
print(sum_result)  # 출력: 8
```

### 📚 함수의 다양한 형태

#### 1) 기본 매개변수 (Default Parameters)

```python
def introduce(name, age=18):
    """
    이름과 나이를 소개
    age의 기본값은 18
    """
    print(f"My name is {name}, I am {age} years old.")

introduce("Bob")           # 출력: My name is Bob, I am 18 years old.
introduce("Carol", 20)     # 출력: My name is Carol, I am 20 years old.
```

**매개변수 타입 표**

| 타입 | 설명 | 예시 |
|------|------|------|
| 위치 매개변수 | 순서대로 전달 | `func(1, 2)` |
| 기본 매개변수 | 기본값 설정 | `func(x, y=10)` |
| 키워드 매개변수 | 이름으로 전달 | `func(x=1, y=2)` |
| 가변 매개변수 | 개수 제한 없음 | `func(*args)` |
| 가변 키워드 | 딕셔너리 형태 | `func(**kwargs)` |

#### 2) 가변 매개변수 (*args)

```python
def sum_all(*numbers):
    """
    여러 개의 숫자를 모두 더하기
    *args는 튜플로 전달됨
    """
    total = 0
    for num in numbers:
        total += num
    return total

print(sum_all(1, 2, 3))           # 출력: 6
print(sum_all(10, 20, 30, 40))    # 출력: 100
```

#### 3) 가변 키워드 매개변수 (**kwargs)

```python
def print_info(**info):
    """
    여러 키-값 쌍의 정보를 출력
    **kwargs는 딕셔너리로 전달됨
    """
    for key, value in info.items():
        print(f"{key}: {value}")

print_info(name="David", age=17, school="High School")
# 출력:
# name: David
# age: 17
# school: High School
```

#### 4) 모든 매개변수 조합

```python
def complete_function(pos1, pos2, default_param=10, *args, **kwargs):
    """
    모든 타입의 매개변수를 사용하는 함수
    """
    print(f"Position 1: {pos1}")
    print(f"Position 2: {pos2}")
    print(f"Default: {default_param}")
    print(f"Additional args: {args}")
    print(f"Keyword args: {kwargs}")

complete_function(1, 2, 20, 30, 40, name="Eve", city="Seoul")
# 출력:
# Position 1: 1
# Position 2: 2
# Default: 20
# Additional args: (30, 40)
# Keyword args: {'name': 'Eve', 'city': 'Seoul'}
```

### 🎯 함수 활용 예시

```python
# 계산기 함수 모음
def calculator(operation, num1, num2):
    """
    간단한 계산기 함수
    operation: 'add', 'subtract', 'multiply', 'divide'
    """
    if operation == "add":
        return num1 + num2
    elif operation == "subtract":
        return num1 - num2
    elif operation == "multiply":
        return num1 * num2
    elif operation == "divide":
        if num2 != 0:
            return num1 / num2
        else:
            return "Cannot divide by zero!"
    else:
        return "Unknown operation"

# 사용 예시
print(calculator("add", 10, 5))        # 출력: 15
print(calculator("multiply", 4, 3))    # 출력: 12
print(calculator("divide", 10, 2))     # 출력: 5.0
```

---

## 5. 모듈과 패키지 (Modules & Packages)

### 📌 개념 이해

**모듈이란?**
- Python 코드를 담고 있는 파일 (.py)
- 함수, 클래스, 변수를 포함
- 다른 프로그램에서 재사용 가능

**패키지란?**
- 여러 모듈을 포함하는 디렉토리
- `__init__.py` 파일로 식별
- 계층적 구조로 구성

### 🔍 모듈 구조

```
my_project/
│
├── main.py
├── math_utils.py          # 모듈
└── my_package/            # 패키지
    ├── __init__.py
    ├── module1.py
    └── module2.py
```

### 💡 모듈 만들기

**math_utils.py 파일 생성**

```python
"""
수학 관련 유틸리티 함수 모듈
"""

def add(a, b):
    """두 수를 더함"""
    return a + b

def subtract(a, b):
    """두 수를 뺌"""
    return a - b

def multiply(a, b):
    """두 수를 곱함"""
    return a * b

PI = 3.14159

class Circle:
    """원 클래스"""
    def __init__(self, radius):
        self.radius = radius
    
    def area(self):
        return PI * self.radius ** 2
```

### 📚 모듈 불러오기 (Import)

| Import 방법 | 설명 | 사용 예시 |
|-------------|------|----------|
| `import module` | 전체 모듈 불러오기 | `module.function()` |
| `from module import func` | 특정 함수만 불러오기 | `func()` |
| `from module import *` | 모든 것 불러오기 | `func()` |
| `import module as alias` | 별칭 사용 | `alias.function()` |

```python
# 방법 1: 전체 모듈 불러오기
import math_utils

result1 = math_utils.add(5, 3)
print(result1)  # 출력: 8


# 방법 2: 특정 함수만 불러오기
from math_utils import add, multiply

result2 = add(10, 20)
print(result2)  # 출력: 30


# 방법 3: 별칭 사용
import math_utils as mu

result3 = mu.subtract(15, 5)
print(result3)  # 출력: 10


# 방법 4: 모든 것 불러오기 (권장하지 않음)
from math_utils import *

circle = Circle(5)
print(circle.area())  # 출력: 78.53975
```

### 🎯 내장 모듈 활용

```python
# 1. math 모듈 - 수학 함수
import math

print(math.sqrt(16))      # 출력: 4.0 (제곱근)
print(math.ceil(3.2))     # 출력: 4 (올림)
print(math.floor(3.8))    # 출력: 3 (내림)


# 2. random 모듈 - 난수 생성
import random

print(random.randint(1, 10))      # 1~10 사이의 정수
print(random.choice([1, 2, 3]))   # 리스트에서 랜덤 선택


# 3. datetime 모듈 - 날짜/시간
from datetime import datetime

now = datetime.now()
print(now)                        # 현재 날짜와 시간
print(now.year)                   # 현재 연도
```

---

## 6. 클래스 (Classes)

### 📌 개념 이해

**클래스란?**
- 객체를 만들기 위한 설계도 (Blueprint)
- 데이터(속성)와 기능(메서드)를 함께 묶음
- 객체 지향 프로그래밍의 핵심

**객체(Object)란?**
- 클래스로부터 만들어진 실체
- 인스턴스(Instance)라고도 함

### 🔍 클래스 구조

```python
class ClassName:
    """클래스 설명"""
    
    # 생성자 (Constructor)
    def __init__(self, parameter):
        self.attribute = parameter
    
    # 메서드 (Method)
    def method_name(self):
        return self.attribute
```

### 📊 클래스 구성 요소

| 구성 요소 | 설명 | 예시 |
|----------|------|------|
| `class` | 클래스 정의 키워드 | `class Student:` |
| `__init__` | 생성자 메서드 | 객체 초기화 |
| `self` | 객체 자신을 가리킴 | 모든 메서드의 첫 매개변수 |
| 속성 (Attribute) | 객체의 데이터 | `self.name` |
| 메서드 (Method) | 객체의 기능 | `def study(self):` |

### 💡 기본 예시

```python
# 예시 1: 간단한 클래스
class Dog:
    """강아지 클래스"""
    
    def __init__(self, name, age):
        """생성자: 강아지 초기화"""
        self.name = name  # 속성
        self.age = age    # 속성
    
    def bark(self):
        """메서드: 짖기"""
        print(f"{self.name}: Woof! Woof!")
    
    def get_info(self):
        """메서드: 정보 반환"""
        return f"Name: {self.name}, Age: {self.age}"

# 객체 생성
my_dog = Dog("Bobby", 3)
your_dog = Dog("Max", 5)

# 메서드 호출
my_dog.bark()                    # 출력: Bobby: Woof! Woof!
print(my_dog.get_info())         # 출력: Name: Bobby, Age: 3
print(your_dog.get_info())       # 출력: Name: Max, Age: 5
```

### 📚 클래스의 심화 개념

#### 1) 클래스 변수 vs 인스턴스 변수

```python
class Student:
    """학생 클래스"""
    
    # 클래스 변수 (모든 학생이 공유)
    school_name = "Python High School"
    student_count = 0
    
    def __init__(self, name, grade):
        # 인스턴스 변수 (각 학생마다 다름)
        self.name = name
        self.grade = grade
        Student.student_count += 1
    
    def introduce(self):
        """자기소개"""
        print(f"I am {self.name}, grade {self.grade}")
        print(f"I study at {Student.school_name}")

# 객체 생성
student1 = Student("Alice", 10)
student2 = Student("Bob", 11)

student1.introduce()
# 출력:
# I am Alice, grade 10
# I study at Python High School

print(f"Total students: {Student.student_count}")
# 출력: Total students: 2
```

**변수 타입 비교**

| 변수 타입 | 위치 | 공유 여부 | 접근 방법 |
|----------|------|----------|----------|
| 클래스 변수 | 클래스 내부, `__init__` 외부 | 모든 객체가 공유 | `ClassName.variable` |
| 인스턴스 변수 | `__init__` 내부 | 각 객체마다 고유 | `self.variable` |

#### 2) 상속 (Inheritance)

```python
# 부모 클래스 (Parent Class)
class Animal:
    """동물 클래스"""
    
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        """기본 소리"""
        print(f"{self.name} makes a sound")

# 자식 클래스 (Child Class)
class Cat(Animal):
    """고양이 클래스 - Animal 상속"""
    
    def speak(self):
        """메서드 오버라이딩"""
        print(f"{self.name}: Meow!")

class Dog(Animal):
    """강아지 클래스 - Animal 상속"""
    
    def speak(self):
        """메서드 오버라이딩"""
        print(f"{self.name}: Woof!")

# 객체 생성 및 사용
cat = Cat("Kitty")
dog = Dog("Buddy")

cat.speak()  # 출력: Kitty: Meow!
dog.speak()  # 출력: Buddy: Woof!
```

#### 3) 특수 메서드 (Magic Methods)

```python
class Book:
    """책 클래스"""
    
    def __init__(self, title, author, pages):
        self.title = title
        self.author = author
        self.pages = pages
    
    def __str__(self):
        """print() 할 때 출력되는 문자열"""
        return f"'{self.title}' by {self.author}"
    
    def __len__(self):
        """len() 함수 사용 시 반환값"""
        return self.pages
    
    def __eq__(self, other):
        """== 연산자 사용 시 비교"""
        return self.title == other.title

# 사용 예시
book1 = Book("Python Basics", "John Doe", 300)
book2 = Book("Python Basics", "Jane Smith", 300)

print(book1)            # 출력: 'Python Basics' by John Doe
print(len(book1))       # 출력: 300
print(book1 == book2)   # 출력: True (제목이 같음)
```

**주요 특수 메서드**

| 메서드 | 설명 | 호출 방법 |
|--------|------|----------|
| `__init__` | 생성자 | `obj = Class()` |
| `__str__` | 문자열 표현 | `print(obj)` |
| `__len__` | 길이 반환 | `len(obj)` |
| `__eq__` | 동등 비교 | `obj1 == obj2` |
| `__add__` | 덧셈 | `obj1 + obj2` |
| `__getitem__` | 인덱싱 | `obj[index]` |

### 🎯 실용적인 클래스 예시

```python
class BankAccount:
    """은행 계좌 클래스"""
    
    def __init__(self, owner, balance=0):
        """
        계좌 생성
        owner: 소유자 이름
        balance: 초기 잔액 (기본값 0)
        """
        self.owner = owner
        self.balance = balance
        self.transaction_history = []
    
    def deposit(self, amount):
        """입금"""
        if amount > 0:
            self.balance += amount
            self.transaction_history.append(f"Deposit: +{amount}")
            print(f"Deposited {amount}. New balance: {self.balance}")
        else:
            print("Invalid deposit amount!")
    
    def withdraw(self, amount):
        """출금"""
        if amount > self.balance:
            print("Insufficient balance!")
        elif amount <= 0:
            print("Invalid withdrawal amount!")
        else:
            self.balance -= amount
            self.transaction_history.append(f"Withdraw: -{amount}")
            print(f"Withdrew {amount}. New balance: {self.balance}")
    
    def get_balance(self):
        """잔액 조회"""
        return f"Current balance: {self.balance}"
    
    def show_history(self):
        """거래 내역 출력"""
        print(f"\n--- Transaction History for {self.owner} ---")
        for transaction in self.transaction_history:
            print(transaction)

# 사용 예시
account = BankAccount("Alice", 1000)
account.deposit(500)      # 입금
account.withdraw(200)     # 출금
print(account.get_balance())  # 잔액 조회
account.show_history()    # 거래 내역
```

---

## 7. 리스트 (List)

### 📌 개념 이해

**리스트란?**
- 순서가 있는 데이터 모음
- 대괄호 `[]` 사용
- 변경 가능(Mutable)
- 다양한 타입 저장 가능

### 📊 리스트 기본 연산

| 연산 | 설명 | 예시 |
|------|------|------|
| 생성 | 리스트 만들기 | `my_list = [1, 2, 3]` |
| 인덱싱 | 요소 접근 | `my_list[0]` |
| 슬라이싱 | 부분 추출 | `my_list[1:3]` |
| 추가 | 요소 추가 | `my_list.append(4)` |
| 삭제 | 요소 제거 | `my_list.remove(2)` |
| 길이 | 요소 개수 | `len(my_list)` |

### 💡 기본 예시

```python
# 리스트 생성
fruits = ["apple", "banana", "cherry"]
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", 3.14, True]

# 인덱싱 (0부터 시작)
print(fruits[0])    # 출력: apple
print(fruits[-1])   # 출력: cherry (뒤에서 첫 번째)

# 슬라이싱
print(numbers[1:4])    # 출력: [2, 3, 4]
print(numbers[:3])     # 출력: [1, 2, 3] (처음부터 3번째 전까지)
print(numbers[2:])     # 출력: [3, 4, 5] (2번째부터 끝까지)
print(numbers[::2])    # 출력: [1, 3, 5] (2칸씩 건너뛰기)
```

### 📚 리스트 메서드

```python
my_list = [3, 1, 4, 1, 5]

# 1. append() - 끝에 추가
my_list.append(9)
print(my_list)  # 출력: [3, 1, 4, 1, 5, 9]

# 2. insert() - 특정 위치에 추가
my_list.insert(0, 10)  # 0번 인덱스에 10 추가
print(my_list)  # 출력: [10, 3, 1, 4, 1, 5, 9]

# 3. remove() - 값으로 제거
my_list.remove(1)  # 첫 번째 1 제거
print(my_list)  # 출력: [10, 3, 4, 1, 5, 9]

# 4. pop() - 인덱스로 제거 및 반환
removed = my_list.pop()  # 마지막 요소 제거
print(removed)  # 출력: 9
print(my_list)  # 출력: [10, 3, 4, 1, 5]

# 5. sort() - 정렬
my_list.sort()
print(my_list)  # 출력: [1, 3, 4, 5, 10]

# 6. reverse() - 역순
my_list.reverse()
print(my_list)  # 출력: [10, 5, 4, 3, 1]

# 7. count() - 개수 세기
count = my_list.count(3)
print(count)  # 출력: 1

# 8. index() - 인덱스 찾기
idx = my_list.index(5)
print(idx)  # 출력: 1
```

**리스트 메서드 요약표**

| 메서드 | 기능 | 반환값 | 원본 변경 |
|--------|------|--------|----------|
| `append(x)` | 끝에 추가 | None | O |
| `insert(i, x)` | i 위치에 추가 | None | O |
| `remove(x)` | x 제거 | None | O |
| `pop(i)` | i 위치 제거 및 반환 | 제거된 값 | O |
| `sort()` | 정렬 | None | O |
| `reverse()` | 역순 | None | O |
| `count(x)` | x 개수 | 정수 | X |
| `index(x)` | x의 인덱스 | 정수 | X |

### 🎯 리스트 활용 예시

```python
# 학생 성적 관리
scores = []

# 성적 추가
scores.append(85)
scores.append(92)
scores.append(78)
scores.append(95)

print(f"Scores: {scores}")

# 평균 계산
average = sum(scores) / len(scores)
print(f"Average: {average}")

# 최고 점수
highest = max(scores)
print(f"Highest score: {highest}")

# 최저 점수
lowest = min(scores)
print(f"Lowest score: {lowest}")

# 정렬
scores.sort()
print(f"Sorted scores: {scores}")

# 출력 결과:
# Scores: [85, 92, 78, 95]
# Average: 87.5
# Highest score: 95
# Lowest score: 78
# Sorted scores: [78, 85, 92, 95]
```

### 🔄 2차원 리스트

```python
# 2차원 리스트 (행렬)
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]

# 접근
print(matrix[0][0])  # 출력: 1 (첫 번째 행, 첫 번째 열)
print(matrix[1][2])  # 출력: 6 (두 번째 행, 세 번째 열)

# 반복문으로 출력
for row in matrix:
    for element in row:
        print(element, end=" ")
    print()  # 줄바꿈

# 출력:
# 1 2 3 
# 4 5 6 
# 7 8 9
```

---

## 8. 딕셔너리 (Dictionary)

### 📌 개념 이해

**딕셔너리란?**
- 키(Key)와 값(Value)의 쌍으로 데이터 저장
- 중괄호 `{}` 사용
- 키는 고유해야 함
- 순서가 없음 (Python 3.7+ 부터는 입력 순서 유지)

### 📊 딕셔너리 기본 연산

| 연산 | 설명 | 예시 |
|------|------|------|
| 생성 | 딕셔너리 만들기 | `my_dict = {"key": "value"}` |
| 접근 | 값 가져오기 | `my_dict["key"]` |
| 추가/수정 | 키-값 추가/변경 | `my_dict["new"] = "value"` |
| 삭제 | 키-값 제거 | `del my_dict["key"]` |
| 존재 확인 | 키 존재 여부 | `"key" in my_dict` |

### 💡 기본 예시

```python
# 딕셔너리 생성
student = {
    "name": "Alice",
    "age": 17,
    "grade": 11,
    "subjects": ["Math", "Science", "English"]
}

# 값 접근
print(student["name"])      # 출력: Alice
print(student["age"])       # 출력: 17

# 값 추가/수정
student["school"] = "Python High"  # 새 키-값 추가
student["age"] = 18                # 기존 값 수정

print(student)
# 출력: {'name': 'Alice', 'age': 18, 'grade': 11, 
#        'subjects': ['Math', 'Science', 'English'], 
#        'school': 'Python High'}

# 값 삭제
del student["grade"]
print(student)
```

### 📚 딕셔너리 메서드

```python
person = {
    "name": "Bob",
    "age": 25,
    "city": "Seoul"
}

# 1. keys() - 모든 키 가져오기
keys = person.keys()
print(keys)  # 출력: dict_keys(['name', 'age', 'city'])

# 2. values() - 모든 값 가져오기
values = person.values()
print(values)  # 출력: dict_values(['Bob', 25, 'Seoul'])

# 3. items() - 모든 키-값 쌍 가져오기
items = person.items()
print(items)  # 출력: dict_items([('name', 'Bob'), ('age', 25), ('city', 'Seoul')])

# 4. get() - 안전하게 값 가져오기
print(person.get("name"))        # 출력: Bob
print(person.get("phone"))       # 출력: None (키가 없어도 에러 안남)
print(person.get("phone", "N/A")) # 출력: N/A (기본값 설정)

# 5. update() - 여러 키-값 추가/수정
person.update({"age": 26, "job": "Developer"})
print(person)

# 6. pop() - 키로 값 제거 및 반환
age = person.pop("age")
print(f"Removed age: {age}")
print(person)
```

**딕셔너리 메서드 요약표**

| 메서드 | 기능 | 반환값 |
|--------|------|--------|
| `keys()` | 모든 키 | dict_keys 객체 |
| `values()` | 모든 값 | dict_values 객체 |
| `items()` | 모든 키-값 쌍 | dict_items 객체 |
| `get(key, default)` | 키의 값 (안전) | 값 또는 None |
| `update(dict)` | 딕셔너리 병합 | None |
| `pop(key)` | 키 제거 및 반환 | 제거된 값 |
| `clear()` | 모든 항목 제거 | None |

### 🎯 딕셔너리 활용 예시

```python
# 영어-한글 사전
dictionary = {
    "apple": "사과",
    "banana": "바나나",
    "cherry": "체리",
    "grape": "포도"
}

# 단어 찾기
word = "apple"
if word in dictionary:
    print(f"{word}: {dictionary[word]}")
else:
    print(f"'{word}' not found")

# 모든 단어 출력
print("\n--- Dictionary ---")
for english, korean in dictionary.items():
    print(f"{english}: {korean}")

# 출력:
# apple: 사과
# 
# --- Dictionary ---
# apple: 사과
# banana: 바나나
# cherry: 체리
# grape: 포도
```

### 🔄 중첩 딕셔너리

```python
# 학생 정보 관리
students = {
    "student1": {
        "name": "Alice",
        "age": 17,
        "scores": {"math": 95, "science": 88}
    },
    "student2": {
        "name": "Bob",
        "age": 18,
        "scores": {"math": 82, "science": 91}
    }
}

# 접근
print(students["student1"]["name"])              # 출력: Alice
print(students["student1"]["scores"]["math"])    # 출력: 95

# 모든 학생 정보 출력
for student_id, info in students.items():
    print(f"\n{student_id}:")
    print(f"  Name: {info['name']}")
    print(f"  Age: {info['age']}")
    print(f"  Math Score: {info['scores']['math']}")
```

---

## 9. 람다 함수 (Lambda)

### 📌 개념 이해

**람다 함수란?**
- 이름 없는 함수 (익명 함수)
- 한 줄로 간단하게 정의
- `lambda` 키워드 사용
- 간단한 함수가 필요할 때 사용

### 🔍 람다 구조

```python
lambda parameters: expression
```

**일반 함수 vs 람다 함수**

```python
# 일반 함수
def add(x, y):
    return x + y

# 람다 함수
add_lambda = lambda x, y: x + y

# 둘 다 같은 결과
print(add(3, 5))         # 출력: 8
print(add_lambda(3, 5))  # 출력: 8
```

### 💡 기본 예시

```python
# 예시 1: 제곱 함수
square = lambda x: x ** 2
print(square(5))  # 출력: 25

# 예시 2: 두 수의 합
add = lambda x, y: x + y
print(add(10, 20))  # 출력: 30

# 예시 3: 조건문 사용
max_value = lambda a, b: a if a > b else b
print(max_value(15, 10))  # 출력: 15

# 예시 4: 여러 매개변수
multiply_three = lambda x, y, z: x * y * z
print(multiply_three(2, 3, 4))  # 출력: 24
```

### 📊 람다 vs 일반 함수 비교

| 특징 | 일반 함수 | 람다 함수 |
|------|----------|----------|
| 정의 키워드 | `def` | `lambda` |
| 이름 | 필수 | 없음 (변수에 할당 가능) |
| 본문 | 여러 줄 가능 | 한 줄만 가능 |
| return | `return` 키워드 필요 | 자동 반환 |
| 사용 시기 | 복잡한 로직 | 간단한 연산 |

### 🎯 람다 활용 예시

```python
# 정렬에 람다 사용
students = [
    {"name": "Alice", "score": 85},
    {"name": "Bob", "score": 92},
    {"name": "Charlie", "score": 78}
]

# 점수로 정렬
sorted_students = sorted(students, key=lambda x: x["score"])
print(sorted_students)
# 출력: [{'name': 'Charlie', 'score': 78}, 
#        {'name': 'Alice', 'score': 85}, 
#        {'name': 'Bob', 'score': 92}]

# 이름으로 정렬
sorted_by_name = sorted(students, key=lambda x: x["name"])
print(sorted_by_name)
```

---

## 10. Map, Filter, Reduce

### 📌 개념 이해

**고차 함수(Higher-Order Function)란?**
- 함수를 인자로 받거나 함수를 반환하는 함수
- `map()`, `filter()`, `reduce()`가 대표적

### 1️⃣ Map 함수

**map이란?**
- 모든 요소에 함수를 적용
- `map(function, iterable)`
- 결과는 map 객체 (리스트로 변환 필요)

```python
# 예시 1: 모든 숫자를 제곱
numbers = [1, 2, 3, 4, 5]
squared = map(lambda x: x ** 2, numbers)
print(list(squared))  # 출력: [1, 4, 9, 16, 25]

# 예시 2: 문자열을 대문자로
words = ["hello", "world", "python"]
upper_words = map(lambda x: x.upper(), words)
print(list(upper_words))  # 출력: ['HELLO', 'WORLD', 'PYTHON']

# 예시 3: 두 리스트 더하기
list1 = [1, 2, 3]
list2 = [10, 20, 30]
result = map(lambda x, y: x + y, list1, list2)
print(list(result))  # 출력: [11, 22, 33]
```

### 2️⃣ Filter 함수

**filter란?**
- 조건에 맞는 요소만 선택
- `filter(function, iterable)`
- 함수가 True를 반환하는 요소만 유지

```python
# 예시 1: 짝수만 선택
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
even_numbers = filter(lambda x: x % 2 == 0, numbers)
print(list(even_numbers))  # 출력: [2, 4, 6, 8, 10]

# 예시 2: 특정 점수 이상 학생
scores = [85, 92, 78, 95, 88, 73]
pass_scores = filter(lambda x: x >= 80, scores)
print(list(pass_scores))  # 출력: [85, 92, 95, 88]

# 예시 3: 문자열 길이로 필터링
words = ["cat", "elephant", "dog", "butterfly"]
long_words = filter(lambda x: len(x) > 5, words)
print(list(long_words))  # 출력: ['elephant', 'butterfly']
```

### 3️⃣ Reduce 함수

**reduce란?**
- 누적 계산 (요소들을 하나의 값으로)
- `reduce(function, iterable)`
- `functools` 모듈에서 import 필요

```python
from functools import reduce

# 예시 1: 모든 숫자의 합
numbers = [1, 2, 3, 4, 5]
total = reduce(lambda x, y: x + y, numbers)
print(total)  # 출력: 15 (1+2+3+4+5)

# 예시 2: 모든 숫자의 곱
product = reduce(lambda x, y: x * y, numbers)
print(product)  # 출력: 120 (1*2*3*4*5)

# 예시 3: 최댓값 찾기
numbers = [5, 2, 9, 1, 7]
maximum = reduce(lambda x, y: x if x > y else y, numbers)
print(maximum)  # 출력: 9
```

### 📊 Map, Filter, Reduce 비교

| 함수 | 목적 | 반환 타입 | 요소 개수 |
|------|------|----------|----------|
| `map()` | 변환 | map 객체 | 입력과 동일 |
| `filter()` | 선택 | filter 객체 | 입력 이하 |
| `reduce()` | 누적 계산 | 단일 값 | 1개 |

### 🎯 종합 예시

```python
# 학생 점수 처리
scores = [75, 82, 91, 68, 95, 73, 88]

# 1. map: 모든 점수에 5점 추가
adjusted = list(map(lambda x: x + 5, scores))
print(f"Adjusted scores: {adjusted}")

# 2. filter: 80점 이상만 선택
high_scores = list(filter(lambda x: x >= 80, adjusted))
print(f"High scores: {high_scores}")

# 3. reduce: 평균 계산
from functools import reduce
total = reduce(lambda x, y: x + y, high_scores)
average = total / len(high_scores)
print(f"Average of high scores: {average}")

# 출력:
# Adjusted scores: [80, 87, 96, 73, 100, 78, 93]
# High scores: [80, 87, 96, 100, 93]
# Average of high scores: 91.2
```

---

## 11. 컴프리헨션 (Comprehension)

### 📌 개념 이해

**컴프리헨션이란?**
- 리스트, 딕셔너리, 집합을 간결하게 생성
- 한 줄로 반복문과 조건문 표현
- 가독성과 효율성 향상

### 1️⃣ 리스트 컴프리헨션

**기본 구조**

```python
[expression for item in iterable]
[expression for item in iterable if condition]
```

```python
# 예시 1: 제곱수 리스트
numbers = [1, 2, 3, 4, 5]

# 일반적인 방법
squares = []
for num in numbers:
    squares.append(num ** 2)
print(squares)  # 출력: [1, 4, 9, 16, 25]

# 컴프리헨션 사용
squares = [num ** 2 for num in numbers]
print(squares)  # 출력: [1, 4, 9, 16, 25]


# 예시 2: 조건문 포함 (짝수만)
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
even_numbers = [num for num in numbers if num % 2 == 0]
print(even_numbers)  # 출력: [2, 4, 6, 8, 10]


# 예시 3: if-else 표현식
numbers = [1, 2, 3, 4, 5]
result = ["Even" if num % 2 == 0 else "Odd" for num in numbers]
print(result)  # 출력: ['Odd', 'Even', 'Odd', 'Even', 'Odd']
```

### 2️⃣ 딕셔너리 컴프리헨션

**기본 구조**

```python
{key_expr: value_expr for item in iterable}
{key_expr: value_expr for item in iterable if condition}
```

```python
# 예시 1: 숫자와 제곱 딕셔너리
numbers = [1, 2, 3, 4, 5]
square_dict = {num: num ** 2 for num in numbers}
print(square_dict)  # 출력: {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}


# 예시 2: 문자열 길이 딕셔너리
words = ["apple", "banana", "cherry"]
length_dict = {word: len(word) for word in words}
print(length_dict)  # 출력: {'apple': 5, 'banana': 6, 'cherry': 6}


# 예시 3: 조건문 포함
numbers = [1, 2, 3, 4, 5, 6]
even_dict = {num: num ** 2 for num in numbers if num % 2 == 0}
print(even_dict)  # 출력: {2: 4, 4: 16, 6: 36}
```

### 3️⃣ 집합 컴프리헨션

**기본 구조**

```python
{expression for item in iterable}
{expression for item in iterable if condition}
```

```python
# 예시 1: 제곱수 집합
numbers = [1, 2, 3, 4, 5]
square_set = {num ** 2 for num in numbers}
print(square_set)  # 출력: {1, 4, 9, 16, 25}


# 예시 2: 중복 제거
numbers = [1, 2, 2, 3, 3, 3, 4, 5, 5]
unique_set = {num for num in numbers}
print(unique_set)  # 출력: {1, 2, 3, 4, 5}
```

### 📊 컴프리헨션 비교표

| 타입 | 괄호 | 예시 |
|------|------|------|
| 리스트 | `[]` | `[x**2 for x in range(5)]` |
| 딕셔너리 | `{}` | `{x: x**2 for x in range(5)}` |
| 집합 | `{}` | `{x**2 for x in range(5)}` |
| 제너레이터 | `()` | `(x**2 for x in range(5))` |

### 🎯 중첩 컴프리헨션

```python
# 2차원 리스트 생성
matrix = [[i * j for j in range(1, 4)] for i in range(1, 4)]
print(matrix)
# 출력: [[1, 2, 3], [2, 4, 6], [3, 6, 9]]

# 2차원 리스트 평탄화
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flattened = [num for row in matrix for num in row]
print(flattened)
# 출력: [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

---

## 12. 예외 처리 (Exception Handling)

### 📌 개념 이해

**예외란?**
- 프로그램 실행 중 발생하는 오류
- 예상치 못한 상황 처리
- 프로그램 비정상 종료 방지

### 🔍 예외 처리 구조

```python
try:
    # 오류가 발생할 수 있는 코드
    pass
except ExceptionType:
    # 오류 발생 시 실행할 코드
    pass
else:
    # 오류가 없을 때 실행 (선택)
    pass
finally:
    # 항상 실행 (선택)
    pass
```

### 💡 기본 예시

```python
# 예시 1: 기본 예외 처리
try:
    number = int(input("Enter a number: "))
    result = 10 / number
    print(f"Result: {result}")
except ZeroDivisionError:
    print("Cannot divide by zero!")
except ValueError:
    print("Please enter a valid number!")

# 예시 2: 모든 예외 처리
try:
    number = int(input("Enter a number: "))
    result = 10 / number
except Exception as e:
    print(f"An error occurred: {e}")


# 예시 3: else와 finally 사용
try:
    number = int(input("Enter a number: "))
    result = 10 / number
except ZeroDivisionError:
    print("Cannot divide by zero!")
else:
    print(f"Result: {result}")
finally:
    print("Execution completed!")
```

### 📊 주요 예외 타입

| 예외 | 설명 | 발생 상황 |
|------|------|----------|
| `ValueError` | 부적절한 값 | `int("abc")` |
| `ZeroDivisionError` | 0으로 나누기 | `10 / 0` |
| `IndexError` | 인덱스 범위 초과 | `list[100]` |
| `KeyError` | 딕셔너리 키 없음 | `dict["없는키"]` |
| `TypeError` | 타입 오류 | `"text" + 5` |
| `FileNotFoundError` | 파일 없음 | `open("없는파일.txt")` |

### 🎯 실용적인 예외 처리

```python
# 안전한 나누기 함수
def safe_divide(a, b):
    """
    안전하게 나누기를 수행하는 함수
    """
    try:
        result = a / b
        return result
    except ZeroDivisionError:
        print("Error: Cannot divide by zero!")
        return None
    except TypeError:
        print("Error: Please provide numbers only!")
        return None

# 사용 예시
print(safe_divide(10, 2))    # 출력: 5.0
print(safe_divide(10, 0))    # 출력: Error: Cannot divide by zero!
                              #       None
print(safe_divide(10, "a"))  # 출력: Error: Please provide numbers only!
                              #       None
```

### 🔧 사용자 정의 예외

```python
# 사용자 정의 예외 클래스
class InvalidAgeError(Exception):
    """나이가 유효하지 않을 때 발생하는 예외"""
    pass

def check_age(age):
    """나이 유효성 검사"""
    if age < 0:
        raise InvalidAgeError("Age cannot be negative!")
    elif age > 150:
        raise InvalidAgeError("Age is too high!")
    else:
        print(f"Valid age: {age}")

# 사용 예시
try:
    check_age(25)     # 정상 실행
    check_age(-5)     # 예외 발생
except InvalidAgeError as e:
    print(f"Error: {e}")
```

---

## 13. 파일 입출력 (File I/O)

### 📌 개념 이해

**파일 입출력이란?**
- 파일에 데이터 저장 (쓰기)
- 파일에서 데이터 읽기 (읽기)
- 데이터 영구 보관

### 📊 파일 모드

| 모드 | 설명 | 파일 없으면 | 파일 있으면 |
|------|------|------------|-----------|
| `'r'` | 읽기 (기본) | 오류 | 읽기 |
| `'w'` | 쓰기 | 생성 | 덮어쓰기 |
| `'a'` | 추가 | 생성 | 끝에 추가 |
| `'r+'` | 읽기+쓰기 | 오류 | 읽기+쓰기 |
| `'w+'` | 쓰기+읽기 | 생성 | 덮어쓰기 |

### 💡 기본 예시

```python
# 예시 1: 파일 쓰기
file = open("example.txt", "w")
file.write("Hello, World!\n")
file.write("This is a text file.\n")
file.close()

# 예시 2: 파일 읽기
file = open("example.txt", "r")
content = file.read()
print(content)
file.close()

# 예시 3: with 문 사용 (권장)
with open("example.txt", "w") as file:
    file.write("Hello, Python!\n")
    file.write("File handling is easy!\n")
# 자동으로 파일 닫힘

with open("example.txt", "r") as file:
    content = file.read()
    print(content)
```

### 📚 파일 읽기 메서드

```python
# 1. read() - 전체 읽기
with open("example.txt", "r") as file:
    content = file.read()
    print(content)

# 2. readline() - 한 줄씩 읽기
with open("example.txt", "r") as file:
    line1 = file.readline()
    line2 = file.readline()
    print(line1, end="")
    print(line2, end="")

# 3. readlines() - 모든 줄을 리스트로
with open("example.txt", "r") as file:
    lines = file.readlines()
    for line in lines:
        print(line, end="")

# 4. 반복문으로 읽기 (효율적)
with open("example.txt", "r") as file:
    for line in file:
        print(line, end="")
```

### 🎯 실용적인 예시

```python
# 학생 성적 저장 및 읽기

# 1. 성적 저장
students = [
    {"name": "Alice", "score": 85},
    {"name": "Bob", "score": 92},
    {"name": "Charlie", "score": 78}
]

with open("scores.txt", "w") as file:
    for student in students:
        file.write(f"{student['name']},{student['score']}\n")

# 2. 성적 읽기 및 처리
print("--- Student Scores ---")
with open("scores.txt", "r") as file:
    total_score = 0
    count = 0
    
    for line in file:
        name, score = line.strip().split(",")
        score = int(score)
        print(f"{name}: {score}")
        total_score += score
        count += 1
    
    average = total_score / count
    print(f"\nAverage Score: {average:.2f}")
```

### 🔧 CSV 파일 처리

```python
import csv

# CSV 쓰기
data = [
    ["Name", "Age", "Grade"],
    ["Alice", 17, 11],
    ["Bob", 18, 12],
    ["Charlie", 16, 10]
]

with open("students.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerows(data)

# CSV 읽기
with open("students.csv", "r") as file:
    reader = csv.reader(file)
    for row in reader:
        print(row)
```

---

## 📝 종합 실습 예제

### 학생 관리 시스템

```python
class Student:
    """학생 클래스"""
    
    def __init__(self, name, age, scores):
        self.name = name
        self.age = age
        self.scores = scores
    
    def get_average(self):
        """평균 계산"""
        return sum(self.scores) / len(self.scores)
    
    def __str__(self):
        return f"{self.name} (Age: {self.age})"

class StudentManager:
    """학생 관리 클래스"""
    
    def __init__(self):
        self.students = []
    
    def add_student(self, student):
        """학생 추가"""
        self.students.append(student)
    
    def get_top_students(self, n=3):
        """상위 n명 학생 반환"""
        sorted_students = sorted(
            self.students, 
            key=lambda s: s.get_average(), 
            reverse=True
        )
        return sorted_students[:n]
    
    def get_statistics(self):
        """통계 정보 반환"""
        all_scores = [s.get_average() for s in self.students]
        return {
            "total": len(self.students),
            "average": sum(all_scores) / len(all_scores),
            "highest": max(all_scores),
            "lowest": min(all_scores)
        }
    
    def save_to_file(self, filename):
        """파일에 저장"""
        with open(filename, "w") as file:
            for student in self.students:
                scores_str = ",".join(map(str, student.scores))
                file.write(f"{student.name},{student.age},{scores_str}\n")
    
    def load_from_file(self, filename):
        """파일에서 읽기"""
        try:
            with open(filename, "r") as file:
                for line in file:
                    parts = line.strip().split(",")
                    name = parts[0]
                    age = int(parts[1])
                    scores = list(map(int, parts[2:]))
                    self.add_student(Student(name, age, scores))
        except FileNotFoundError:
            print(f"File '{filename}' not found!")

# 사용 예시
manager = StudentManager()

# 학생 추가
manager.add_student(Student("Alice", 17, [85, 90, 88]))
manager.add_student(Student("Bob", 18, [92, 87, 95]))
manager.add_student(Student("Charlie", 16, [78, 82, 80]))

# 상위 학생
print("Top 2 Students:")
for student in manager.get_top_students(2):
    print(f"  {student}: {student.get_average():.2f}")

# 통계
stats = manager.get_statistics()
print(f"\nStatistics:")
print(f"  Total Students: {stats['total']}")
print(f"  Average Score: {stats['average']:.2f}")
print(f"  Highest: {stats['highest']:.2f}")
print(f"  Lowest: {stats['lowest']:.2f}")

# 파일 저장
manager.save_to_file("students_data.txt")
print("\nData saved to file!")
```

---

## 🎓 학습 정리

### 핵심 개념 요약

1. **출력문과 입력**: print()와 input() 활용
2. **반복문**: for, while을 통한 반복 처리
3. **Random**: 난수 생성 및 무작위 선택
4. **함수**: 재사용 가능한 코드 블록
5. **모듈**: 함수와 클래스를 담은 파일
6. **클래스**: 객체를 만드는 설계도
7. **리스트**: 순서가 있는 데이터 모음
8. **딕셔너리**: 키-값 쌍의 데이터
9. **람다**: 간단한 익명 함수
10. **Map/Filter/Reduce**: 함수형 프로그래밍
11. **컴프리헨션**: 간결한 데이터 생성
12. **예외 처리**: 오류 상황 대처
13. **파일 입출력**: 데이터 영구 저장

### 학습 로드맵

```
기초 문법 (출력, 입력)
    ↓
반복문 (for, while)
    ↓
Random 함수
    ↓
함수와 모듈
    ↓
클래스와 객체
    ↓
자료구조 (리스트, 딕셔너리)
    ↓
함수형 프로그래밍 (람다, map, filter)
    ↓
컴프리헨션
    ↓
예외 처리
    ↓
파일 입출력
    ↓
실전 프로젝트
```

### 다음 학습 주제

- 데코레이터 (Decorator)
- 제너레이터 (Generator)
- 정규 표현식 (Regular Expression)
- 멀티스레딩/멀티프로세싱
- 웹 크롤링
- 데이터 분석 (Pandas, NumPy)

---

**작성일:** 2024년 12월 17일  
**대상:** 고등학생 코딩 학습자  
**난이도:** 기초~중급  
**학습 시간:** 약 15-20시간


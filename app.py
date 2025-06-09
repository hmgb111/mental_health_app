import streamlit as st
from datetime import date
from datetime import datetime

# ✅ Google Sheets 연동 관련 라이브러리
import gspread
from google.oauth2.service_account import Credentials

# ✅ Google Sheets 저장 함수
def save_to_gsheet(data: dict):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file("creds.json", scopes=scopes)
    client = gspread.authorize(creds)

    # ✅ 여기에 본인의 시트 ID를 넣어주세요
    SPREADSHEET_ID = "1RLDHvjDLCItLm7n-snwYPWgCwsT5eMjSAEgZqRlLZfU"
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    # ✅ 제출 시간 추가
    data["제출시간"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ✅ 데이터 저장, 시트 헤더 순서에 맞춰 value 뽑기
    values = [data.get(key, "") for key in sheet.row_values(1)]
    sheet.append_row(values)

# 세션 상태 초기화
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'tool' not in st.session_state:
    st.session_state.tool = ''
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}
if 'responses' not in st.session_state:
    st.session_state.responses = []

# 검사 도구별 문항, 점수, 해석 기준 정의
TOOLS = {
    "BAI": {
        "questions": [
            "어지러움", "손이 떨림", "불안하거나 두려운 느낌", "안정되지 않음",
            "무서운 일이 일어날 것 같은 느낌", "심장이 빠르게 뜀", "숨이 막힘",
            "질식할 것 같은 느낌", "가슴이 답답함", "창피당할까 봐 두려움",
            "얼굴이 화끈거림", "차가운 땀", "손발이 차가움", "쓰러질 것 같은 느낌",
            "정신이 멍해짐", "죽을 것 같은 공포", "기절할 것 같음",
            "근육이 긴장됨", "짜증남", "배가 불편함", "호흡이 가빠짐"
        ],
        "score_map": {
            "전혀 그렇지 않다": 0,
            "조금 그렇다": 1,
            "상당히 그렇다": 2,
            "매우 그렇다": 3
        },
        "interpretation": [
            (0, 7, "불안 없음"),
            (8, 15, "경미한 불안"),
            (16, 25, "중등도 불안"),
            (26, 63, "심한 불안")
        ]
    },
    "BDI": {
        "questions": [
            "슬프다", "앞으로 일이 잘못될 것 같다", "나는 실패자처럼 느껴진다",
            "예전만큼 만족감을 느끼지 못한다", "죄책감을 느낀다", "벌을 받아야 한다고 느낀다",
            "나 자신에게 실망했다", "나는 다른 사람보다 못하다", "죽고 싶다는 생각이 든다",
            "전에 비해 더 많이 울게 된다", "화가 나거나 짜증이 난다", "결정 내리기 어렵다",
            "전에 비해 일에 대한 관심이 줄었다", "쓸모없는 사람처럼 느껴진다",
            "힘이 없다", "잠을 잘 수 없다", "피로를 느낀다", "식욕이 없다",
            "체중이 줄었다", "건강에 대해 걱정된다", "성생활에 대한 관심이 줄었다"
        ],
        "score_map": {
            "전혀 아니다": 0,
            "약간 그렇다": 1,
            "상당히 그렇다": 2,
            "매우 그렇다": 3
        },
        "interpretation": [
            (0, 13, "우울 없음"),
            (14, 19, "가벼운 우울"),
            (20, 28, "중등도 우울"),
            (29, 63, "심한 우울")
        ]
    },
    "SSI": {
        "questions": [
            "자살하고 싶다는 생각이 전혀 없다", "죽고 싶다는 생각이 들 때가 있다",
            "자살할 수 있는 구체적 방법을 생각해본 적이 있다", "자살 계획을 세운 적이 있다",
            "자살 시도를 생각한 적이 있다", "자살하고 싶은 충동을 느낀 적이 있다",
            "자살에 대한 소망이 강해진 적이 있다", "자살 준비 행동을 한 적이 있다",
            "가족이나 친구에게 유서를 남긴 적이 있다", "자살을 시도했거나 실행하려 한 적이 있다",
            "치료받은 적이 있다", "의도적으로 상해를 입힌 적이 있다", "자살에 대한 생각이 자주 든다",
            "자살 충동을 억제하기 어렵다", "현재 자살에 대한 생각이 있다",
            "가족에게 자신이 자살 생각을 하고 있다는 걸 암시한 적 있다",
            "사후세계에 대해 자주 생각한다", "스스로를 무가치하다고 느낀다", "살 이유가 없다고 느낀다"
        ],
        "score_map": {
            "전혀 아니다": 0,
            "약간 그렇다": 1,
            "상당히 그렇다": 2,
            "매우 그렇다": 3
        },
        "interpretation": [
            (0, 8, "자살위험 낮음"),
            (9, 19, "자살위험 중간"),
            (20, 38, "자살위험 높음")
        ]
    },
    "GDS": {
        "questions": [
            "01 쓸데없는 생각들이 자꾸 떠올라 괴롭다.", "02 아무것도 할 수 없을 것처럼 무기력하게 느껴진다.",
            "03 안절부절 못하고 초조할 때가 자주 있다.", "04 밖에 나가기 보다는 주로 집에 있으려 한다.",
            "05 앞날에 대해 걱정할 때가 많다.", "06 지금 내가 살아있다는 것이 참 기쁘다.",
            "07 인생은 즐거운 것이다.", "08 아침에 기분 좋게 일어난다.",
            "09 예전처럼 정신이 맑다.", "10 건강에 대해서 걱정하는 일이 별로 없다.",
            "11 내 판단력은 여전히 좋다.", "12 내 나이의 다른 사람들 못지 않게 건강하다.",
            "13 사람들과 잘 어울린다.", "14 정말 자신이 없다.", "15 즐겁고 행복하다.", "16 내 기억력은 괜찮은 것 같다.", 
            "17 지쳐버리지나 않을까 걱정된다.", "18 별일없이 얼굴이 화끈거리고 진땀이 날 때가 있다.", 
            "19 농담을 들어도 재미가 없다.", "20 예전에 좋아하던 일들을 여전히 즐긴다.", "21 기분이 좋은 편이다.", 
            "22 앞날에 대해 희망적으로 느낀다.", "23 사람들이 나를 싫어한다고 느낀다.", "24 나의 잘못에 대하여 항상 나 자신을 탓한다.", 
            "25 전부다 화가 나고 짜증이 날 때가 많다.", "26 전보다 내모습이 추해졌다고 생각한다.", 
            "27 어떤 일을 시작하려면 예전보다 힘이 많이 든다.", "28 무슨 일을 하던지 곧 피곤해진다.", 
            "29 요즈음 몸무게가 많이 줄었다.", "30 이성에 대해 여전히 관심이 있다."
        ],
        "score_map": {
            "예": 1,
            "아니오": 0
        },
        "interpretation": [
            (0, 13, "정상"),
            (14, 18, "우울의심 및 가벼운 우울증"),
            (19, 21, "중등도"),
            (22, 30, "심한 우울증")
            #최저 0점에서 최고 30점까지
            #14점을 최적절한 점수로 보고, 14점에서 18점 사이는 우울의심 및 가벼운 우울증, 
            #19점에서 21점 사이는 중도의 우울증, 22점 이상은 심한 우울증으로 분류되는데, 점수가 높을수록 우울 정도가 심한 것을 의미한다.
        ]
    }
}

# 페이지 1
from datetime import date  # 상단 import 필요

def page1():
    st.title("정신건강 자가검사")
    st.subheader("검사 선택 및 개인정보 입력")

    # 🔹 검사 도구 선택
    tool = st.selectbox("검사 도구 선택",["", "BAI", "BDI", "SSI", "GDS"],
        index=["", "BAI", "BDI", "SSI", "GDS"].index(st.session_state.tool)
        if st.session_state.tool else 0)

    # 🔹 기본 개인정보 입력
    name = st.text_input("이름", value=st.session_state.user_info.get("이름", ""))
    gender = st.radio("성별", ["남", "여"],
        index=["남", "여"].index(st.session_state.user_info.get("성별", "남"))
        if st.session_state.user_info.get("성별") else None)
    birth = st.date_input("생년월일", value=date.fromisoformat(st.session_state.user_info.get("생년월일", "2000-01-01")),
        min_value=date(1900, 1, 1), max_value=date.today())
    pid = st.text_input("환자등록번호", value=st.session_state.user_info.get("환자등록번호", ""))
    exam_date = st.date_input("검사 날짜", value=date.fromisoformat(st.session_state.user_info.get("검사날짜", str(date.today()))))

    # 🔹 다음 버튼 클릭 시 상태 저장
    if st.button("다음"):
        if tool and name and pid:
            st.session_state.tool = tool
            st.session_state.user_info = {
                "이름": name,
                "성별": gender,
                "생년월일": str(birth),
                "환자등록번호": pid,
                "검사날짜": str(exam_date)
            }
            st.session_state.step = 2
        else:
            st.warning("모든 항목은 필수입니다.")

# 페이지 2
# 🔹 도구별 설명문 정의
TOOL_DESCRIPTIONS = {
    "BAI": """🧠 **BAI (Beck Anxiety Inventory)**

본 검사는 현재의 **불안 정도와 양상**을 평가하기 위한 심리 검사입니다.  
정확한 평가를 위해 솔직하게 응답해 주시고, 불안하거나 궁금한 사항은 언제든 문의해주세요.""",

    "BDI": """🌧 **BDI (Beck Depression Inventory)**

본 검사는 **우울감의 정도와 관련된 정서적・인지적 증상**을 평가하기 위한 심리 검사입니다본 검사는 **우울감의 정도와 관련된 정서적・인지적 증상**을 평가하기 위한 심리 검사입니다. 
각각의 질문을 잘 읽으시고, 오늘을 포함한 최근 2주 간 느꼈던 기분에 가장 가까운 진술 하나만을 선택해주세요. 
각각의 질문을 잘 읽으시고, 오늘을 포함한 최근 2주 간 느꼈던 기분에 가장 가까운 진술 하나만을 선택해주세요.""",

    "SSI": """⚠️ **SSI (Suicidal Ideation Inventory)**

최근 며칠 간의 **자살 사고 및 관련 행동**에 대해 묻는 척도입니다.  
솔직한 응답이 매우 중요합니다.""",

    "GDS": """🌿 **GDS (Geriatric Depression Scale)**

이 검사는 노년기 우울증 여부를 확인하기 위한 **예/아니오형 자가검사**입니다.  
각 문항에 대해 해당하는 답을 선택해주세요."""
}

def page2():
    st.title(f"{st.session_state.tool} 검사")
    # 🔹 도구별 설명 표시
    description = TOOL_DESCRIPTIONS.get(st.session_state.tool, "")
    if description:
        st.markdown(description)
    tool_data = TOOLS[st.session_state.tool]
    questions = tool_data["questions"]
    score_map = tool_data["score_map"]
    reverse_score_map = {v: k for k, v in score_map.items()}  # 역매핑: 숫자 → 응답 문자열

    # 🔹 환자 정보 표시
    st.markdown("---")
    st.caption("※ 입력된 환자 정보 확인 후 오류가 있을 시 뒤로가기를 클릭하여 수정해주세요.")
    st.markdown(
        f"""
        **이름**: {st.session_state.user_info['이름']}  
        **성별**: {st.session_state.user_info['성별']}  
        **생년월일**: {st.session_state.user_info['생년월일']}  
        **환자등록번호**: {st.session_state.user_info['환자등록번호']}  
        **검사날짜**: {st.session_state.user_info['검사날짜']}
        """
    )
    # 🔹 뒤로가기 버튼
    if st.button("뒤로가기"):
        st.session_state.step = 1
        st.rerun()
    st.markdown("---")

    # 🔹 응답 저장소 초기화
    if len(st.session_state.responses) != len(questions):
        st.session_state.responses = [None] * len(questions)
    
    # 🔹 문항 표시 + 응답 유지
    for i, q in enumerate(questions):
        prev = st.session_state.responses[i]
        key_name = f"{st.session_state.tool}_q{i}"
        options = list(score_map.keys())
        default_value = reverse_score_map.get(prev) if prev is not None else None

        ans = st.radio(
            f"{i+1}. {q}",
            options,
            index=options.index(default_value) if default_value in options else None,
            key=key_name
        )
        if ans is not None:
            st.session_state.responses[i] = score_map[ans]
    
    # 🔹 제출 버튼    
    st.markdown("---")
    st.caption("※ 제출 전 문항을 다시 한번 확인해주세요. 제출시 수정이 불가합니다.")
    if st.button("제출"):
        if None in st.session_state.responses:
            st.warning("모든 문항에 응답해 주세요.")
        else:
            total = sum(st.session_state.responses)
            interp = next((text for (low, high, text) in tool_data["interpretation"] if low <= total <= high), "")
            st.session_state.result = {
                "검사 도구": st.session_state.tool,
                "총점": total,
                "해석": interp,
                **st.session_state.user_info
            }
            # st.write(st.session_state.result)  ← 결과 저장 또는 출력 용도

            save_to_gsheet(st.session_state.result)  # <- 구글 시트 저장
            st.session_state.step = 3                  # 다음 페이지로 이동
            st.rerun()                                 # 페이지 전환 적용

def page3():
    st.success("✅ 제출이 완료되었습니다. 의료진에게 태블릿을 제출해주세요.")
    st.markdown("""
            <div style="background-color:#d4edda; padding: 15px; border-left: 5px solid #28a745; border-radius: 5px; color: #155724; text-align: left;">
            응답해주신 모든 정보는 의료 상담, 진단, 치료 목적 외에는 사용되지 않으며,<br>
            개인정보 보호법 및 의료법에 따라 철저히 보호됩니다.<br>
            검사 결과는 <b>성가의원 내부</b>에서만 활용되며, <b>외부에 유출되지 않습니다</b>.
            </div>
            """, unsafe_allow_html=True)
    st.markdown("---")

    # 🏠 홈으로 돌아가기 버튼
    if st.button("🏠 새로 검사 시작하기"):
        # 모든 상태 초기화
        st.session_state.step = 1
        st.session_state.tool = ''
        st.session_state.user_info = {}
        st.session_state.responses = []
        st.session_state.result = None
        st.rerun()

# 페이지 라우팅
if st.session_state.step == 1:
    page1()
elif st.session_state.step == 2:
    page2()
elif st.session_state.step == 3:
    page3()
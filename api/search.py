import json
import os
import re
import sys

from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from google import genai


# ==========================================
# 기본 설정
# ==========================================

PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "auctions.json"
)

LOCAL_ENV_PATH = (
    PROJECT_ROOT
    / ".env.local"
)

GEMINI_MODEL = "gemini-3.1-flash-lite"


# ==========================================
# 로컬 환경변수 읽기
# ==========================================

def load_local_env():

    """
    vercel dev 또는 일반 Python 실행 시
    GEMINI_API_KEY가 환경변수에 없다면
    .env.local에서 읽어온다.

    실제 Vercel 배포환경에서는
    Vercel Environment Variable이 우선한다.
    """

    if os.environ.get("GEMINI_API_KEY"):
        return


    if not LOCAL_ENV_PATH.exists():
        return


    with open(
        LOCAL_ENV_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if (
                not line
                or line.startswith("#")
                or "=" not in line
            ):
                continue


            key, value = line.split(
                "=",
                1
            )


            key = key.strip()
            value = value.strip()


            if key == "GEMINI_API_KEY":

                os.environ[
                    "GEMINI_API_KEY"
                ] = value

                break


load_local_env()


# ==========================================
# 지역 표준화
# ==========================================

REGION_ALIASES = {

    "서울": [
        "서울",
        "서울특별시",
    ],

    "부산": [
        "부산",
        "부산광역시",
    ],

    "대구": [
        "대구",
        "대구광역시",
    ],

    "인천": [
        "인천",
        "인천광역시",
    ],

    "광주": [
        "광주",
        "광주광역시",
    ],

    "대전": [
        "대전",
        "대전광역시",
    ],

    "울산": [
        "울산",
        "울산광역시",
    ],

    "세종": [
        "세종",
        "세종특별자치시",
    ],

    "경기": [
        "경기",
        "경기도",
    ],

    "강원": [
        "강원",
        "강원특별자치도",
    ],

    "충북": [
        "충북",
        "충청북도",
    ],

    "충남": [
        "충남",
        "충청남도",
    ],

    "전북": [
        "전북",
        "전북특별자치도",
    ],

    "전남": [
        "전남",
        "전라남도",
    ],

    "경북": [
        "경북",
        "경상북도",
    ],

    "경남": [
        "경남",
        "경상남도",
    ],

    "제주": [
        "제주",
        "제주특별자치도",
    ],
}


# ==========================================
# 자산 분류
# ==========================================

CATEGORY_KEYWORDS = {

    "부동산": [
        "부동산",
        "아파트",
        "토지",
        "상가",
        "오피스텔",
        "공장",
        "단독주택",
        "다가구주택",
        "창고",
    ],

    "채권": [
        "채권",
        "대여금",
        "매출채권",
        "구상금",
        "보증금반환",
        "손해배상",
        "공사대금",
    ],

    "지식재산권": [
        "지식재산",
        "지재권",
        "특허",
        "특허권",
        "상표",
        "상표권",
        "디자인권",
        "저작권",
        "프로그램저작권",
    ],

    "주식": [
        "주식",
        "비상장주식",
        "상장주식",
    ],

    "자동차": [
        "자동차",
        "차량",
        "승용차",
        "화물차",
    ],

    "기계기구": [
        "기계",
        "기계기구",
        "장비",
        "설비",
    ],

    "동산": [
        "동산",
        "집기",
        "재고",
        "미술품",
    ],
}


SUBCATEGORY_KEYWORDS = [

    "아파트",
    "토지",
    "상가",
    "오피스텔",
    "공장",
    "단독주택",
    "다가구주택",
    "창고",

    "특허권",
    "상표권",
    "디자인권",
    "프로그램저작권",

    "비상장주식",
    "상장주식",

    "승용차",
    "화물차",
]


# ==========================================
# Gemini Structured Output Schema
# ==========================================

SEARCH_SCHEMA = {

    "type": "object",

    "properties": {

        "regions": {
            "type": "array",

            "items": {
                "type": "string"
            }
        },

        "category": {
            "type": "string"
        },

        "subcategory": {
            "type": "string"
        },

        "max_price": {
            "type": "integer"
        },

        "min_price": {
            "type": "integer"
        },

        "bid_within_days": {
            "type": "integer"
        },

        "sort": {
            "type": "string"
        },
    },

    "required": [
        "regions",
        "category",
        "subcategory",
        "max_price",
        "min_price",
        "bid_within_days",
        "sort",
    ],
}


# ==========================================
# 샘플 DB 읽기
# ==========================================

def load_auctions():

    with open(
        DATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)


    return data["auctions"]


# ==========================================
# 한국어 금액 처리
# Gemini 장애 테스트용 규칙 분석에서 사용
# ==========================================

def parse_korean_amount(text):

    total = 0
    matched = False


    # 4억원 / 1억
    eok_match = re.search(
        r"(\d+(?:\.\d+)?)\s*억",
        text
    )


    if eok_match:

        total += int(
            float(
                eok_match.group(1)
            )
            * 100_000_000
        )

        matched = True


    # 5천만원
    cheonman_match = re.search(
        r"(\d+(?:\.\d+)?)\s*천\s*만\s*원?",
        text
    )


    if cheonman_match:

        total += int(
            float(
                cheonman_match.group(1)
            )
            * 10_000_000
        )

        matched = True

    else:

        # 3500만원
        manwon_match = re.search(
            r"(\d[\d,]*(?:\.\d+)?)\s*만\s*원?",
            text
        )


        if manwon_match:

            value = float(
                manwon_match
                .group(1)
                .replace(",", "")
            )


            total += int(
                value * 10_000
            )

            matched = True


    # 50000000원
    if not matched:

        won_match = re.search(
            r"(\d[\d,]+)\s*원",
            text
        )


        if won_match:

            total = int(
                won_match
                .group(1)
                .replace(",", "")
            )

            matched = True


    if matched:
        return total


    return None


# ==========================================
# 규칙 기반 검색조건 분석
#
# Gemini 장애 여부를 확인할 때 사용할 수 있도록
# 남겨둔다.
# ==========================================

def parse_query_simple(query):

    normalized_query = (
        query
        .replace("·", " ")
        .replace("/", " ")
    )


    # --------------------------
    # 지역
    # --------------------------

    regions = []


    for region, aliases in (
        REGION_ALIASES.items()
    ):

        if any(
            alias in normalized_query
            for alias in aliases
        ):

            regions.append(
                region
            )


    # --------------------------
    # 자산 대분류
    # --------------------------

    category = None


    for (
        category_name,
        keywords
    ) in CATEGORY_KEYWORDS.items():

        if any(
            keyword in normalized_query
            for keyword in keywords
        ):

            category = (
                category_name
            )

            break


    # --------------------------
    # 세부분류
    # --------------------------

    subcategory = None


    for keyword in (
        SUBCATEGORY_KEYWORDS
    ):

        if keyword in normalized_query:

            subcategory = keyword

            break


    # --------------------------
    # 가격
    # --------------------------

    amount = parse_korean_amount(
        normalized_query
    )


    max_price = None
    min_price = None


    if amount is not None:

        if any(
            keyword
            in normalized_query

            for keyword in [
                "이하",
                "이내",
                "미만",
                "까지",
                "안쪽",
                "넘지 않는",
            ]
        ):

            max_price = amount


        elif any(
            keyword
            in normalized_query

            for keyword in [
                "이상",
                "초과",
            ]
        ):

            min_price = amount


        else:

            max_price = amount


    # --------------------------
    # 입찰기간
    # --------------------------

    days_match = re.search(
        r"(?:앞으로\s*)?"
        r"(\d+)\s*일\s*"
        r"(?:이내|안|내)",
        normalized_query
    )


    bid_within_days = None


    if days_match:

        bid_within_days = int(
            days_match.group(1)
        )


    # --------------------------
    # 정렬
    # --------------------------

    sort = "bid_date"


    if any(
        keyword in normalized_query

        for keyword in [
            "저렴",
            "싼",
            "최저가 낮",
            "가격 낮",
            "제일 싼",
        ]
    ):

        sort = "minimum_price"


    return {
        "regions":
            regions,

        "category":
            category,

        "subcategory":
            subcategory,

        "max_price":
            max_price,

        "min_price":
            min_price,

        "bid_within_days":
            bid_within_days,

        "sort":
            sort,
    }


# ==========================================
# Gemini 결과 표준화
# ==========================================

def normalize_conditions(
    conditions
):

    # --------------------------
    # 지역
    # --------------------------

    normalized_regions = []


    for value in (
        conditions.get(
            "regions",
            []
        )
        or []
    ):

        value = str(
            value
        )


        for (
            standard_region,
            aliases
        ) in REGION_ALIASES.items():

            if any(
                alias in value
                for alias in aliases
            ):

                if (
                    standard_region
                    not in normalized_regions
                ):

                    normalized_regions.append(
                        standard_region
                    )

                break


    # --------------------------
    # 카테고리
    # --------------------------

    category = (
        conditions.get(
            "category",
            ""
        )
        or ""
    ).strip()


    if category:

        normalized_category = None


        for (
            standard_category,
            keywords
        ) in CATEGORY_KEYWORDS.items():

            if (
                category
                == standard_category
                or any(
                    keyword in category
                    for keyword in keywords
                )
            ):

                normalized_category = (
                    standard_category
                )

                break


        category = (
            normalized_category
            or category
        )

    else:

        category = None


    # --------------------------
    # 세부분류
    # --------------------------

    subcategory = (
        conditions.get(
            "subcategory",
            ""
        )
        or ""
    ).strip()


    if not subcategory:

        subcategory = None


    # 특허라고만 반환한 경우
    if subcategory == "특허":
        subcategory = "특허권"


    if subcategory == "상표":
        subcategory = "상표권"


    # 세부분류를 통해 대분류 보정
    if (
        subcategory
        in [
            "특허권",
            "상표권",
            "디자인권",
            "프로그램저작권",
        ]
    ):

        category = "지식재산권"


    if (
        subcategory
        in [
            "아파트",
            "토지",
            "상가",
            "오피스텔",
            "공장",
            "단독주택",
            "다가구주택",
            "창고",
        ]
    ):

        category = "부동산"


    # --------------------------
    # 숫자
    # --------------------------

    def normalize_number(
        value
    ):

        if value in [
            None,
            "",
            0,
            "0",
        ]:

            return None


        try:

            return int(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return None


    max_price = normalize_number(
        conditions.get(
            "max_price"
        )
    )


    min_price = normalize_number(
        conditions.get(
            "min_price"
        )
    )


    bid_within_days = (
        normalize_number(
            conditions.get(
                "bid_within_days"
            )
        )
    )


    # --------------------------
    # 정렬
    # --------------------------

    sort = (
        conditions.get(
            "sort",
            "bid_date"
        )
        or "bid_date"
    )


    if sort not in [
        "bid_date",
        "minimum_price",
    ]:

        sort = "bid_date"


    return {
        "regions":
            normalized_regions,

        "category":
            category,

        "subcategory":
            subcategory,

        "max_price":
            max_price,

        "min_price":
            min_price,

        "bid_within_days":
            bid_within_days,

        "sort":
            sort,
    }


# ==========================================
# Gemini 자연어 분석
# ==========================================

def parse_query_with_gemini(
    query
):

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )


    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY 환경변수가 "
            "설정되지 않았습니다."
        )


    system_instruction = """
사용자의 파산재단 매각물건 검색 요청에서
검색조건만 추출하세요.

사용자가 말하지 않은 조건은
임의로 추가하지 마세요.

반드시 지정된 JSON 스키마에 맞게 반환하세요.

지역 표준명:
서울, 부산, 대구, 인천, 광주, 대전, 울산,
세종, 경기, 강원, 충북, 충남, 전북, 전남,
경북, 경남, 제주

자산 대분류:
부동산, 채권, 지식재산권, 주식,
자동차, 기계기구, 동산

조건이 없을 경우:
regions = []
category = ""
subcategory = ""
max_price = 0
min_price = 0
bid_within_days = 0

가격은 반드시 원 단위 정수로 변환하세요.

예:
5천만원 = 50000000
4억원 = 400000000
1억 5천만원 = 150000000

이하, 이내, 안쪽, 넘지 않는다는 표현은
max_price로 처리합니다.

이상, 초과는
min_price로 처리합니다.

특허 또는 특허권은:
category = "지식재산권"
subcategory = "특허권"

상표 또는 상표권은:
category = "지식재산권"
subcategory = "상표권"

한 달 = 30일
2주 = 14일

가격이 낮은 물건을 원하는 경우:
sort = "minimum_price"

그 외에는:
sort = "bid_date"
"""


    # SDK 연결을 요청마다 생성하고
    # 응답 후 명시적으로 종료한다.
    client = genai.Client(
        api_key=api_key
    )


    try:

        response = (
            client.models.generate_content(

                model=
                    GEMINI_MODEL,

                contents=
                    query,

                config={

                    "system_instruction":
                        system_instruction,

                    "response_mime_type":
                        "application/json",

                    "response_json_schema":
                        SEARCH_SCHEMA,
                },
            )
        )


        if not response.text:

            raise RuntimeError(
                "Gemini가 검색조건을 "
                "반환하지 않았습니다."
            )


        conditions = json.loads(
            response.text
        )


        return normalize_conditions(
            conditions
        )


    finally:

        client.close()


# ==========================================
# 세부유형 검색
# ==========================================

def matches_subcategory(
    asset,
    subcategory
):

    if not subcategory:
        return True


    details = asset.get(
        "details",
        {}
    )


    candidates = [

        asset.get(
            "subcategory",
            ""
        ),

        details.get(
            "property_type",
            ""
        ),

        details.get(
            "ip_type",
            ""
        ),
    ]


    return any(
        subcategory == candidate
        or subcategory in candidate

        for candidate in candidates

        if candidate
    )


# ==========================================
# 추천 이유 생성
# ==========================================

def make_reason(
    item,
    conditions
):

    reasons = []


    if conditions["regions"]:

        reasons.append(
            "요청한 지역 조건에 "
            "부합합니다"
        )


    if conditions["category"]:

        reasons.append(
            f"{conditions['category']} "
            f"물건입니다"
        )


    if conditions["max_price"]:

        reasons.append(
            "설정한 최대가격 "
            "이내입니다"
        )


    if conditions["min_price"]:

        reasons.append(
            "설정한 최소가격 "
            "이상입니다"
        )


    if (
        conditions[
            "bid_within_days"
        ]
    ):

        reasons.append(
            f"앞으로 "
            f"{conditions['bid_within_days']}"
            f"일 이내 입찰 예정입니다"
        )


    if not reasons:

        reasons.append(
            "검색 조건과 관련성이 "
            "높은 물건입니다"
        )


    return (
        ". ".join(reasons)
        + "."
    )


# ==========================================
# 실제 DB 검색
# ==========================================

def search_auctions(
    auctions,
    conditions,
    limit=6
):

    today = date.today()

    results = []


    for item in auctions:

        asset = item["asset"]
        sale = item["sale"]

        location = asset.get(
            "location",
            ""
        )


        # --------------------------
        # 지역
        # --------------------------

        if conditions["regions"]:

            region_match = False


            for region in (
                conditions["regions"]
            ):

                aliases = (
                    REGION_ALIASES[
                        region
                    ]
                )


                if any(
                    alias in location
                    for alias in aliases
                ):

                    region_match = True

                    break


            if not region_match:
                continue


        # --------------------------
        # 자산 대분류
        # --------------------------

        if (
            conditions["category"]
            and asset.get(
                "category"
            )
            != conditions[
                "category"
            ]
        ):

            continue


        # --------------------------
        # 자산 세부분류
        # --------------------------

        if not matches_subcategory(
            asset,
            conditions[
                "subcategory"
            ]
        ):

            continue


        # --------------------------
        # 최저입찰가격
        # --------------------------

        minimum_price = (
            asset.get(
                "minimum_price"
            )
            or 0
        )


        if (
            conditions[
                "max_price"
            ]
            is not None

            and minimum_price
            > conditions[
                "max_price"
            ]
        ):

            continue


        if (
            conditions[
                "min_price"
            ]
            is not None

            and minimum_price
            < conditions[
                "min_price"
            ]
        ):

            continue


        # --------------------------
        # 입찰기간
        # --------------------------

        if (
            conditions[
                "bid_within_days"
            ]
            is not None
        ):

            try:

                bid_date = (
                    date.fromisoformat(
                        sale[
                            "bid_date"
                        ]
                    )
                )

            except (
                ValueError,
                TypeError
            ):

                continue


            last_date = (
                today
                + timedelta(
                    days=conditions[
                        "bid_within_days"
                    ]
                )
            )


            if (
                bid_date < today
                or bid_date > last_date
            ):

                continue


        results.append(
            item
        )


    # ======================================
    # 정렬
    # ======================================

    if (
        conditions["sort"]
        == "minimum_price"
    ):

        results.sort(

            key=lambda item:
            item["asset"].get(
                "minimum_price",
                0
            )

        )

    else:

        results.sort(

            key=lambda item:
            item["sale"].get(
                "bid_date",
                "9999-12-31"
            )

        )


    return results[:limit]


# ==========================================
# 프론트 전달용 데이터 생성
# ==========================================

def serialize_result(
    item,
    conditions
):

    asset = item["asset"]
    sale = item["sale"]
    trustee = item["trustee"]


    return {

        "id":
            item["id"],

        "category":
            asset["category"],

        "subcategory":
            asset["subcategory"],

        "title":
            asset["title"],

        "location":
            asset["location"],

        "reference_value":
            asset[
                "reference_value"
            ],

        "minimum_price":
            asset[
                "minimum_price"
            ],

        "price_ratio":
            asset.get(
                "price_ratio"
            ),

        "court":
            item["court"],

        "case_number":
            item["case_number"],

        "debtor_name":
            item["debtor_name"],

        "round":
            sale["round"],

        "bid_date":
            sale["bid_date"],

        "method":
            sale["method"],

        "deposit_rate":
            sale["deposit_rate"],

        "trustee_name":
            trustee["name"],

        "trustee_phone":
            trustee["phone"],

        "recommendation_reason":
            make_reason(
                item,
                conditions
            ),
    }


# ==========================================
# 전체 검색 처리
# ==========================================

def process_search(
    query
):

    # ======================================
    # AI 자연어 분석
    # ======================================

    conditions = (
        parse_query_with_gemini(
            query
        )
    )


    # Gemini 테스트 중 문제가 발생하면
    # 아래 코드로 임시 전환 가능
    #
    # conditions = parse_query_simple(
    #     query
    # )


    # ======================================
    # DB 읽기
    # ======================================

    auctions = load_auctions()


    # ======================================
    # 실제 검색
    # ======================================

    results = search_auctions(
        auctions,
        conditions
    )


    serialized_results = [

        serialize_result(
            item,
            conditions
        )

        for item in results

    ]


    return {

        "query":
            query,

        "ai": {

            "used":
                True,

            "model":
                GEMINI_MODEL,
        },

        "conditions":
            conditions,

        "count":
            len(
                serialized_results
            ),

        "results":
            serialized_results,
    }


# ==========================================
# Vercel Serverless Function
# ==========================================

class handler(
    BaseHTTPRequestHandler
):

    # ======================================
    # JSON 응답
    # ======================================

    def send_json(
        self,
        data,
        status=200
    ):

        response = json.dumps(
            data,
            ensure_ascii=False
        ).encode(
            "utf-8"
        )


        self.send_response(
            status
        )


        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )


        self.send_header(
            "Content-Length",
            str(
                len(response)
            )
        )


        self.end_headers()


        self.wfile.write(
            response
        )


    # ======================================
    # GET
    # API 상태 확인용
    # ======================================

    def do_GET(self):

        api_key_exists = bool(
            os.environ.get(
                "GEMINI_API_KEY"
            )
        )


        self.send_json(
            {

                "status":
                    "ok",

                "message":
                    "A1-3 search API is running.",

                "gemini_key_configured":
                    api_key_exists,

                "gemini_model":
                    GEMINI_MODEL,
            }
        )


    # ======================================
    # POST
    # 실제 AI 검색
    # ======================================

    def do_POST(self):

        try:

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )


            raw_body = (
                self.rfile.read(
                    content_length
                )
            )


            body = json.loads(
                raw_body.decode(
                    "utf-8"
                )
            )


            query = (
                body
                .get(
                    "query",
                    ""
                )
                .strip()
            )


            # ------------------------------
            # 빈 입력
            # ------------------------------

            if not query:

                self.send_json(
                    {
                        "error":
                            "검색 조건을 "
                            "입력해주세요."
                    },
                    status=400
                )

                return


            # ------------------------------
            # AI + DB 검색
            # ------------------------------

            result = process_search(
                query
            )


            # ------------------------------
            # 정상 응답
            # ------------------------------

            self.send_json(
                result
            )


        except json.JSONDecodeError:

            self.send_json(
                {
                    "error":
                        "요청 데이터 형식이 "
                        "올바르지 않습니다."
                },
                status=400
            )


        except Exception as error:

            # 상세 오류는 서버 터미널에만 출력
            print(
                "Search API Error:",
                repr(error),
                flush=True
            )


            # 사용자에게는 민감한 정보 미노출
            self.send_json(
                {
                    "error":
                        "AI 검색 중 오류가 "
                        "발생했습니다. "
                        "잠시 후 다시 "
                        "시도해주세요.",

                    "error_type":
                        type(
                            error
                        ).__name__,
                },
                status=500
            )


# ==========================================
# 터미널 직접 테스트
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "검색 문장을 "
            "입력해주세요."
        )


        print(
            '예: python api/search.py '
            '"대전하고 세종에서 '
            '5천만원 이하 '
            '부동산 찾아줘"'
        )


        sys.exit(1)


    test_query = (
        sys.argv[1]
    )


    try:

        result = process_search(
            test_query
        )


        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )


    except Exception as error:

        print(
            "ERROR:",
            type(error).__name__,
            str(error)
        )

        raise
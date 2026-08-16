import json
import re
import sys

from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler
from pathlib import Path


# ==========================================
# 데이터 파일
# ==========================================

DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "auctions.json"
)


# ==========================================
# 검색 기준
# ==========================================

REGION_ALIASES = {
    "서울": ["서울", "서울특별시"],
    "부산": ["부산", "부산광역시"],
    "대구": ["대구", "대구광역시"],
    "인천": ["인천", "인천광역시"],
    "광주": ["광주", "광주광역시"],
    "대전": ["대전", "대전광역시"],
    "울산": ["울산", "울산광역시"],
    "세종": ["세종", "세종특별자치시"],
    "경기": ["경기", "경기도"],
    "강원": ["강원", "강원특별자치도"],
    "충북": ["충북", "충청북도"],
    "충남": ["충남", "충청남도"],
    "전북": ["전북", "전북특별자치도"],
    "전남": ["전남", "전라남도"],
    "경북": ["경북", "경상북도"],
    "경남": ["경남", "경상남도"],
    "제주": ["제주", "제주특별자치도"],
}


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
# JSON 데이터 읽기
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
# 한국어 금액 분석
# ==========================================

def parse_korean_amount(text):

    total = 0
    matched = False


    # 예: 4억원 / 1억원
    eok_match = re.search(
        r"(\d+(?:\.\d+)?)\s*억",
        text
    )

    if eok_match:

        total += int(
            float(eok_match.group(1))
            * 100_000_000
        )

        matched = True


    # 예: 5천만원
    cheonman_match = re.search(
        r"(\d+(?:\.\d+)?)\s*천\s*만\s*원?",
        text
    )

    if cheonman_match:

        total += int(
            float(cheonman_match.group(1))
            * 10_000_000
        )

        matched = True

    else:

        # 예: 3500만원
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


    # 예: 50000000원
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
# 임시 자연어 분석
# Gemini 연결 전 사용
# ==========================================

def parse_query_simple(query):

    normalized_query = (
        query
        .replace("·", " ")
        .replace("/", " ")
    )


    # ------------------
    # 지역
    # ------------------

    regions = []

    for region, aliases in REGION_ALIASES.items():

        if any(
            alias in normalized_query
            for alias in aliases
        ):
            regions.append(region)


    # ------------------
    # 자산 대분류
    # ------------------

    category = None

    for (
        category_name,
        keywords
    ) in CATEGORY_KEYWORDS.items():

        if any(
            keyword in normalized_query
            for keyword in keywords
        ):
            category = category_name
            break


    # ------------------
    # 자산 세부분류
    # ------------------

    subcategory = None

    for keyword in SUBCATEGORY_KEYWORDS:

        if keyword in normalized_query:

            subcategory = keyword
            break


    # ------------------
    # 가격
    # ------------------

    amount = parse_korean_amount(
        normalized_query
    )

    max_price = None
    min_price = None


    if amount is not None:

        if any(
            keyword in normalized_query
            for keyword in [
                "이하",
                "이내",
                "미만",
                "까지",
            ]
        ):

            max_price = amount


        elif any(
            keyword in normalized_query
            for keyword in [
                "이상",
                "초과",
            ]
        ):

            min_price = amount


        else:

            # 별도 표현이 없으면
            # 최대 예산으로 해석
            max_price = amount


    # ------------------
    # 입찰일
    # ------------------

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


    # ------------------
    # 정렬
    # ------------------

    sort = "bid_date"


    if any(
        keyword in normalized_query
        for keyword in [
            "저렴",
            "낮은 가격",
            "가격 낮",
            "최저가 낮",
            "싼",
        ]
    ):

        sort = "minimum_price"


    elif any(
        keyword in normalized_query
        for keyword in [
            "입찰일",
            "가까운",
            "빠른",
        ]
    ):

        sort = "bid_date"


    return {
        "regions": regions,
        "category": category,
        "subcategory": subcategory,
        "max_price": max_price,
        "min_price": min_price,
        "bid_within_days": bid_within_days,
        "sort": sort,
    }


# ==========================================
# 세부분류 검색
# ==========================================

def matches_subcategory(
    asset,
    subcategory
):

    if not subcategory:
        return True


    candidates = [
        asset.get(
            "subcategory",
            ""
        ),

        asset
        .get("details", {})
        .get(
            "property_type",
            ""
        ),

        asset
        .get("details", {})
        .get(
            "ip_type",
            ""
        ),
    ]


    return subcategory in candidates


# ==========================================
# 추천 이유
# ==========================================

def make_reason(
    item,
    conditions
):

    reasons = []


    if conditions["regions"]:
        reasons.append(
            "요청한 지역 조건에 부합합니다"
        )


    if conditions["category"]:
        reasons.append(
            f"{conditions['category']} 물건입니다"
        )


    if conditions["max_price"]:

        reasons.append(
            "설정한 최대가격 이내입니다"
        )


    if conditions["bid_within_days"]:

        reasons.append(
            f"앞으로 "
            f"{conditions['bid_within_days']}일 "
            f"이내 입찰 예정입니다"
        )


    if not reasons:

        reasons.append(
            "검색 조건과 관련성이 높은 물건입니다"
        )


    return ". ".join(reasons) + "."


# ==========================================
# 검색
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


        # ------------------
        # 지역
        # ------------------

        if conditions["regions"]:

            region_match = False

            for region in conditions["regions"]:

                aliases = REGION_ALIASES[
                    region
                ]

                if any(
                    alias in location
                    for alias in aliases
                ):

                    region_match = True
                    break


            if not region_match:
                continue


        # ------------------
        # 대분류
        # ------------------

        if (
            conditions["category"]
            and asset.get("category")
            != conditions["category"]
        ):
            continue


        # ------------------
        # 세부분류
        # ------------------

        if not matches_subcategory(
            asset,
            conditions["subcategory"]
        ):
            continue


        # ------------------
        # 최저입찰가
        # ------------------

        minimum_price = (
            asset.get(
                "minimum_price"
            )
            or 0
        )


        if (
            conditions["max_price"]
            is not None
            and minimum_price
            > conditions["max_price"]
        ):
            continue


        if (
            conditions["min_price"]
            is not None
            and minimum_price
            < conditions["min_price"]
        ):
            continue


        # ------------------
        # 입찰일
        # ------------------

        if (
            conditions["bid_within_days"]
            is not None
        ):

            bid_date = date.fromisoformat(
                sale["bid_date"]
            )

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


        results.append(item)


    # ======================================
    # 정렬
    # ======================================

    if (
        conditions["sort"]
        == "minimum_price"
    ):

        results.sort(
            key=lambda item:
            item["asset"][
                "minimum_price"
            ]
        )

    else:

        results.sort(
            key=lambda item:
            item["sale"][
                "bid_date"
            ]
        )


    return results[:limit]


# ==========================================
# 프론트에 보낼 데이터 정리
# ==========================================

def serialize_result(
    item,
    conditions
):

    asset = item["asset"]
    sale = item["sale"]
    trustee = item["trustee"]


    return {
        "id": item["id"],

        "category":
            asset["category"],

        "subcategory":
            asset["subcategory"],

        "title":
            asset["title"],

        "location":
            asset["location"],

        "reference_value":
            asset["reference_value"],

        "minimum_price":
            asset["minimum_price"],

        "price_ratio":
            asset["price_ratio"],

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
# 실제 검색 실행
# ==========================================

def process_search(query):

    conditions = parse_query_simple(
        query
    )

    auctions = load_auctions()


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
        "query": query,
        "conditions": conditions,
        "count": len(
            serialized_results
        ),
        "results": serialized_results,
    }


# ==========================================
# Vercel Serverless Function
# ==========================================

class handler(
    BaseHTTPRequestHandler
):

    def send_json(
        self,
        data,
        status=200
    ):

        response = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")


        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.end_headers()

        self.wfile.write(
            response
        )


    def do_POST(self):

        try:

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )


            raw_body = self.rfile.read(
                content_length
            )


            body = json.loads(
                raw_body.decode(
                    "utf-8"
                )
            )


            query = (
                body
                .get("query", "")
                .strip()
            )


            if not query:

                self.send_json(
                    {
                        "error":
                            "검색 조건을 입력해주세요."
                    },
                    status=400
                )

                return


            result = process_search(
                query
            )


            self.send_json(
                result
            )


        except json.JSONDecodeError:

            self.send_json(
                {
                    "error":
                        "요청 데이터 형식이 올바르지 않습니다."
                },
                status=400
            )


        except Exception as error:

            print(
                "Search API Error:",
                error
            )

            self.send_json(
                {
                    "error":
                        "검색 중 오류가 발생했습니다."
                },
                status=500
            )


# ==========================================
# 터미널 직접 테스트
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "검색 문장을 입력해주세요."
        )

        print(
            '예: python api/search.py '
            '"대전에 있는 5천만원 이하 '
            '부동산 찾아줘"'
        )

        sys.exit(1)


    test_query = sys.argv[1]


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
    
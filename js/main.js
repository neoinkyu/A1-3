const themeToggle = document.getElementById("theme-toggle");

const savedTheme = localStorage.getItem("theme");

if (savedTheme === "dark") {
  document.documentElement.setAttribute("data-theme", "dark");

  if (themeToggle) {
    themeToggle.textContent = "☀️";
  }
}


if (themeToggle) {

  themeToggle.addEventListener("click", () => {

    const currentTheme =
      document.documentElement.getAttribute("data-theme");

    if (currentTheme === "dark") {

      document.documentElement.removeAttribute("data-theme");

      localStorage.setItem("theme", "light");

      themeToggle.textContent = "🌙";

    } else {

      document.documentElement.setAttribute(
        "data-theme",
        "dark"
      );

      localStorage.setItem("theme", "dark");

      themeToggle.textContent = "☀️";
    }

  });

}

/* ==============================
   Search Page
================================ */

const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchButton = document.getElementById("search-button");

const characterCount =
  document.getElementById("character-count");

const searchMessage =
  document.getElementById("search-message");

const loadingSection =
  document.getElementById("loading-section");

const conditionSection =
  document.getElementById("condition-section");

const resultsSection =
  document.getElementById("results-section");

const conditionList =
  document.getElementById("condition-list");

const auctionResults =
  document.getElementById("auction-results");

const resultCount =
  document.getElementById("result-count");


/* URL의 example 파라미터 처리 */

if (searchInput) {

  const params =
    new URLSearchParams(window.location.search);

  const exampleQuery =
    params.get("example");

  if (exampleQuery) {
    searchInput.value = exampleQuery;
  }

}


/* 글자수 표시 */

function updateCharacterCount() {

  if (!searchInput || !characterCount) {
    return;
  }

  characterCount.textContent =
    `${searchInput.value.length} / 300`;

}


if (searchInput) {

  searchInput.addEventListener(
    "input",
    updateCharacterCount
  );

  updateCharacterCount();

}


/* 검색 예시 버튼 */

const quickSearchButtons =
  document.querySelectorAll(".quick-search-button");


quickSearchButtons.forEach((button) => {

  button.addEventListener("click", () => {

    if (!searchInput) {
      return;
    }

    searchInput.value =
      button.dataset.query;

    updateCharacterCount();

    searchInput.focus();

  });

});


/* 숫자를 원화 형태로 출력 */

function formatPrice(price) {

  if (price >= 100000000) {

    const eok =
      price / 100000000;

    return `${eok.toLocaleString("ko-KR")}억원`;

  }

  if (price >= 10000) {

    const manwon =
      price / 10000;

    return `${manwon.toLocaleString("ko-KR")}만원`;

  }

  return `${price.toLocaleString("ko-KR")}원`;

}


/* 현재는 UI 테스트용 임시 검색 결과 */

const demoResults = [
  {
    category: "부동산",
    title: "대전광역시 유성구 소재 토지",
    location: "대전광역시 유성구 봉명동 123-1",
    minimumPrice: 35000000,
    court: "대전지방법원",
    round: 2,
    bidDate: "2026-09-10",
    caseNumber: "2026하합1001",
    reason:
      "요청한 지역과 자산 유형에 부합하며 최저가격이 5천만원 이하입니다."
  },

  {
    category: "부동산",
    title: "대전광역시 서구 소재 상가",
    location: "대전광역시 서구 둔산동 245-2",
    minimumPrice: 42000000,
    court: "대전지방법원",
    round: 3,
    bidDate: "2026-09-18",
    caseNumber: "2026하단1012",
    reason:
      "예산 범위 안에 있으며 3회차 매각으로 가격 조건이 상대적으로 낮습니다."
  },

  {
    category: "부동산",
    title: "세종특별자치시 소재 토지",
    location: "세종특별자치시 나성동 138-4",
    minimumPrice: 48000000,
    court: "대전지방법원",
    round: 2,
    bidDate: "2026-09-25",
    caseNumber: "2026하합1027",
    reason:
      "검색 범위에 포함된 세종 지역의 부동산이며 설정한 예산을 충족합니다."
  }
];


/* 조건 표시 */

function renderConditions() {

  if (!conditionList) {
    return;
  }

  const conditions = [
    ["지역", "대전 · 세종"],
    ["자산유형", "부동산"],
    ["최대가격", "5,000만원"],
    ["정렬", "입찰일 가까운 순"]
  ];


  conditionList.innerHTML =
    conditions
      .map(([label, value]) => `
        <div class="condition-chip">
          <strong>${label}</strong>
          &nbsp;${value}
        </div>
      `)
      .join("");

}


/* 검색 결과 표시 */

function renderResults() {

  if (!auctionResults || !resultCount) {
    return;
  }


  resultCount.textContent =
    `${demoResults.length}건`;


  auctionResults.innerHTML =
    demoResults
      .map((item) => `

        <article class="auction-card">

          <div class="auction-card-top">

            <span class="asset-badge">
              ${item.category}
            </span>

            <span>
              ${item.round}회차
            </span>

          </div>


          <h3>${item.title}</h3>

          <p class="auction-location">
            ${item.location}
          </p>


          <div class="auction-price">

            <span>최저입찰가</span>

            <strong>
              ${formatPrice(item.minimumPrice)}
            </strong>

          </div>


          <dl class="auction-info">

            <div>
              <dt>관할법원</dt>
              <dd>${item.court}</dd>
            </div>

            <div>
              <dt>사건번호</dt>
              <dd>${item.caseNumber}</dd>
            </div>

            <div>
              <dt>입찰일</dt>
              <dd>${item.bidDate}</dd>
            </div>

            <div>
              <dt>입찰회차</dt>
              <dd>${item.round}회</dd>
            </div>

          </dl>


          <p class="recommendation-text">
            <strong>추천 이유</strong><br>
            ${item.reason}
          </p>

        </article>

      `)
      .join("");

}


/* 검색 실행 */

if (searchForm) {

  searchForm.addEventListener(
    "submit",
    (event) => {

      event.preventDefault();


      const query =
        searchInput.value.trim();


      searchMessage.hidden = true;

      conditionSection.hidden = true;
      resultsSection.hidden = true;


      /* 빈 입력 처리 */

      if (!query) {

        searchMessage.textContent =
          "검색 조건을 입력해주세요.";

        searchMessage.classList.add("error");

        searchMessage.hidden = false;

        searchInput.focus();

        return;

      }


      /* 버튼 중복 클릭 방지 */

      searchButton.disabled = true;

      searchButton.textContent =
        "검색 중...";


      loadingSection.hidden = false;


      /*
        현재는 API를 아직 연결하지 않았기 때문에
        1.2초 후 임시 결과를 표시한다.
      */

      setTimeout(() => {

        loadingSection.hidden = true;

        renderConditions();
        renderResults();

        conditionSection.hidden = false;
        resultsSection.hidden = false;


        searchButton.disabled = false;

        searchButton.innerHTML =
          `AI로 검색하기 <span aria-hidden="true">→</span>`;


        conditionSection.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });

      }, 1200);

    }
  );

}
/* ==============================
   Dark Mode
================================ */

const themeToggle =
  document.getElementById("theme-toggle");

const savedTheme =
  localStorage.getItem("theme");


if (savedTheme === "dark") {

  document.documentElement.setAttribute(
    "data-theme",
    "dark"
  );

  if (themeToggle) {
    themeToggle.textContent = "☀️";
  }

}


if (themeToggle) {

  themeToggle.addEventListener(
    "click",
    () => {

      const currentTheme =
        document.documentElement.getAttribute(
          "data-theme"
        );


      if (currentTheme === "dark") {

        document.documentElement.removeAttribute(
          "data-theme"
        );

        localStorage.setItem(
          "theme",
          "light"
        );

        themeToggle.textContent = "🌙";

      } else {

        document.documentElement.setAttribute(
          "data-theme",
          "dark"
        );

        localStorage.setItem(
          "theme",
          "dark"
        );

        themeToggle.textContent = "☀️";
      }

    }
  );

}


/* ==============================
   Search Page Elements
================================ */

const searchForm =
  document.getElementById("search-form");

const searchInput =
  document.getElementById("search-input");

const searchButton =
  document.getElementById("search-button");

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


/* ==============================
   URL Example Query
================================ */

if (searchInput) {

  const params =
    new URLSearchParams(
      window.location.search
    );

  const exampleQuery =
    params.get("example");


  if (exampleQuery) {

    searchInput.value =
      exampleQuery;

  }

}


/* ==============================
   Character Counter
================================ */

function updateCharacterCount() {

  if (
    !searchInput
    || !characterCount
  ) {
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


/* ==============================
   Quick Search
================================ */

const quickSearchButtons =
  document.querySelectorAll(
    ".quick-search-button"
  );


quickSearchButtons.forEach(
  (button) => {

    button.addEventListener(
      "click",
      () => {

        if (!searchInput) {
          return;
        }


        searchInput.value =
          button.dataset.query;


        updateCharacterCount();

        searchInput.focus();

      }
    );

  }
);


/* ==============================
   Price Formatter
================================ */

function formatPrice(price) {

  if (
    price === null
    || price === undefined
  ) {
    return "-";
  }


  if (price >= 100000000) {

    const eok =
      Math.floor(
        price / 100000000
      );

    const remainder =
      price % 100000000;


    if (remainder >= 10000) {

      const manwon =
        Math.floor(
          remainder / 10000
        );


      return (
        `${eok}억 `
        + `${manwon.toLocaleString("ko-KR")}만원`
      );

    }


    return `${eok}억원`;

  }


  if (price >= 10000) {

    const manwon =
      Math.floor(
        price / 10000
      );


    return (
      `${manwon.toLocaleString("ko-KR")}만원`
    );

  }


  return (
    `${price.toLocaleString("ko-KR")}원`
  );

}


/* ==============================
   Message
================================ */

function showMessage(
  message,
  type = "error"
) {

  if (!searchMessage) {
    return;
  }


  searchMessage.textContent =
    message;


  searchMessage.classList.remove(
    "error"
  );


  if (type === "error") {

    searchMessage.classList.add(
      "error"
    );

  }


  searchMessage.hidden =
    false;

}


function hideMessage() {

  if (!searchMessage) {
    return;
  }


  searchMessage.hidden =
    true;

}


/* ==============================
   Condition Rendering
================================ */

function renderConditions(
  conditions
) {

  if (!conditionList) {
    return;
  }


  const items = [];


  if (
    conditions.regions
    && conditions.regions.length > 0
  ) {

    items.push([
      "지역",
      conditions.regions.join(" · ")
    ]);

  }


  if (conditions.category) {

    items.push([
      "자산유형",
      conditions.category
    ]);

  }


  if (conditions.subcategory) {

    items.push([
      "세부유형",
      conditions.subcategory
    ]);

  }


  if (conditions.max_price) {

    items.push([
      "최대가격",
      formatPrice(
        conditions.max_price
      )
    ]);

  }


  if (conditions.min_price) {

    items.push([
      "최소가격",
      formatPrice(
        conditions.min_price
      )
    ]);

  }


  if (conditions.bid_within_days) {

    items.push([
      "입찰기간",
      `${conditions.bid_within_days}일 이내`
    ]);

  }


  if (
    conditions.sort
    === "minimum_price"
  ) {

    items.push([
      "정렬",
      "최저가 낮은 순"
    ]);

  } else {

    items.push([
      "정렬",
      "입찰일 가까운 순"
    ]);

  }


  if (items.length === 0) {

    items.push([
      "검색",
      "전체 물건"
    ]);

  }


  conditionList.innerHTML =
    items
      .map(
        ([label, value]) => `
          <div class="condition-chip">
            <strong>${label}</strong>
            &nbsp;${value}
          </div>
        `
      )
      .join("");

}


/* ==============================
   Result Rendering
================================ */

function renderResults(
  results
) {

  if (
    !auctionResults
    || !resultCount
  ) {
    return;
  }


  resultCount.textContent =
    `${results.length}건`;


  if (results.length === 0) {

    auctionResults.innerHTML = `
      <div class="result-empty">

        <strong>
          조건에 맞는 매각물건을 찾지 못했습니다.
        </strong>

        <p>
          지역이나 가격 조건을 넓혀서
          다시 검색해보세요.
        </p>

      </div>
    `;

    return;

  }


  auctionResults.innerHTML =
    results
      .map(
        (item, index) => `

          <article
            class="auction-card"
            style="animation-delay:
              ${index * 0.06}s"
          >

            <div class="auction-card-top">

              <span class="asset-badge">
                ${item.category}
              </span>

              <span>
                ${item.round}회차
              </span>

            </div>


            <h3>
              ${item.title}
            </h3>


            <p class="auction-location">
              ${item.location}
            </p>


            <div class="auction-price">

              <span>
                최저입찰가
              </span>

              <strong>
                ${formatPrice(
                  item.minimum_price
                )}
              </strong>

              <small class="auction-reference-price">
                기준가
                ${formatPrice(
                  item.reference_value
                )}
              </small>

            </div>


            <dl class="auction-info">

              <div>
                <dt>관할법원</dt>
                <dd>
                  ${item.court}
                </dd>
              </div>

              <div>
                <dt>사건번호</dt>
                <dd>
                  ${item.case_number}
                </dd>
              </div>

              <div>
                <dt>입찰일</dt>
                <dd>
                  ${item.bid_date}
                </dd>
              </div>

              <div>
                <dt>입찰회차</dt>
                <dd>
                  ${item.round}회
                </dd>
              </div>

              <div>
                <dt>입찰방식</dt>
                <dd>
                  ${item.method}
                </dd>
              </div>

              <div>
                <dt>입찰보증금</dt>
                <dd>
                  ${item.deposit_rate}%
                </dd>
              </div>

              <div>
                <dt>파산관재인</dt>
                <dd>
                  ${item.trustee_name}
                </dd>
              </div>

              <div>
                <dt>관재인 연락처</dt>
                <dd>
                  ${item.trustee_phone}
                </dd>
              </div>

            </dl>


            <p class="recommendation-text">

              <strong>
                추천 이유
              </strong>

              <br>

              ${item.recommendation_reason}

            </p>

          </article>

        `
      )
      .join("");

}


/* ==============================
   API Request
================================ */

async function requestAuctionSearch(
  query
) {

  const controller =
    new AbortController();


  const timeout =
    setTimeout(
      () => controller.abort(),
      30000
    );


  try {

    const response =
      await fetch(
        "/api/search",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({
            query: query
          }),

          signal:
            controller.signal
        }
      );


    let data;


    try {

      data =
        await response.json();

    } catch {

      throw new Error(
        "서버 응답을 처리할 수 없습니다."
      );

    }


    if (!response.ok) {

      throw new Error(
        data.error
        || "검색 요청에 실패했습니다."
      );

    }


    return data;


  } finally {

    clearTimeout(
      timeout
    );

  }

}


/* ==============================
   Search Submit
================================ */

if (searchForm) {

  searchForm.addEventListener(
    "submit",
    async (event) => {

      event.preventDefault();


      const query =
        searchInput.value.trim();


      hideMessage();


      if (conditionSection) {
        conditionSection.hidden = true;
      }


      if (resultsSection) {
        resultsSection.hidden = true;
      }


      /* --------------------------
         Empty Input
      -------------------------- */

      if (!query) {

        showMessage(
          "검색 조건을 입력해주세요."
        );

        searchInput.focus();

        return;

      }


      /* --------------------------
         Loading
      -------------------------- */

      if (searchButton) {

        searchButton.disabled =
          true;

        searchButton.textContent =
          "검색 중...";

      }


      if (loadingSection) {

        loadingSection.hidden =
          false;

      }


      try {

        /* --------------------------
           Real Python API Call
        -------------------------- */

        const data =
          await requestAuctionSearch(
            query
          );


        /* --------------------------
           Render
        -------------------------- */

        renderConditions(
          data.conditions
        );


        renderResults(
          data.results
        );


        if (conditionSection) {

          conditionSection.hidden =
            false;

        }


        if (resultsSection) {

          resultsSection.hidden =
            false;

        }


        if (conditionSection) {

          conditionSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
          });

        }


      } catch (error) {

        if (
          error.name
          === "AbortError"
        ) {

          showMessage(
            "응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."
          );

        } else {

          console.error(
            error
          );


          showMessage(
            error.message
            || "검색 중 오류가 발생했습니다."
          );

        }


      } finally {

        if (loadingSection) {

          loadingSection.hidden =
            true;

        }


        if (searchButton) {

          searchButton.disabled =
            false;

          searchButton.innerHTML =
            `AI로 검색하기
             <span aria-hidden="true">→</span>`;

        }

      }

    }
  );

}
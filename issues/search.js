// original source:
// * https://codepen.io/a-luna/pen/GRooENM
// * https://aaronluna.dev/blog/add-search-to-static-site-lunrjs-hugo-vanillajs/

let pagesIndex, searchIndex;
const MAX_SUMMARY_LENGTH = 100;
const SENTENCE_BOUNDARY_REGEX = /\b\.\s/gm;
const WORD_REGEX = /\b(\w*)[\W|\s|\b]?/gm;

async function fetchJsonData(url) {
  try {
    const response = await fetch(url);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching JSON:', error);
    return null;
  }
}

async function initSearchIndex() {
  try {
    fetchJsonData('/' + BASE_DIR + 'search.json').then(p => {
      pagesIndex = p
    });
    fetchJsonData('/' + BASE_DIR + 'search_idx.json').then(s => {
      searchIndex = lunr.Index.load(s)
    });
  } catch (e) {
    console.log(e);
  }
}

function handleSearchQuery(event) {
  event.preventDefault();
  const query = document.getElementById("search").value.trim().toLowerCase();
  if (!query) {
    // do nothing
    return;
  }
  const results = searchSite(query);
  renderSearchResults(query, results);
}

function searchSite(query) {
  const originalQuery = query;
  query = getLunrSearchQuery(query);
  let results = getSearchResults(query);
  return results.length ?
    results :
    query !== originalQuery ?
    getSearchResults(originalQuery) :
    [];
}

function getSearchResults(query) {
  return searchIndex.search(query).flatMap((hit) => {
    if (hit.ref == "undefined") return [];
    let pageMatch = pagesIndex.filter((page) => page.href === hit.ref)[0];
    pageMatch.score = hit.score;
    return [pageMatch];
  });
}

function getLunrSearchQuery(query) {
  const searchTerms = query.split(" ");
  if (searchTerms.length === 1) {
    return query;
  }
  query = "";
  for (const term of searchTerms) {
    query += `+${term} `;
  }
  return query.trim();
}

function renderSearchResults(query, results) {
  if (!results.length) {
    search_html = "<p>Keine Ergebnisse.</p>"
  } else {
    const results_li = results
      .map(
        (hit) => `
    <div class="search-result-item" data-score="${hit.score.toFixed(2)}">
      <h2><a href="${hit.href}" class="search-result-page-title">${hit.title}</a></h2>
      <p>${createSearchResultBlurb(query, hit.content)}</p>
    </div>
    <hr>
    `
      )
      .join("");
    const count_str = "<p>" + results.length + " " + (results.length > 1 ? "Ergebnisse" : "Ergebnis") + "</p>";
    search_html = count_str + results_li;
  }
  document.querySelector(".main_content").innerHTML = search_html;
  document.body.className = "search";
}

function createSearchResultBlurb(query, pageContent) {
  const searchQueryRegex = new RegExp(createQueryStringRegex(query), "gmi");
  const searchQueryHits = Array.from(
    pageContent.matchAll(searchQueryRegex),
    (m) => m.index
  );
  const sentenceBoundaries = Array.from(
    pageContent.matchAll(SENTENCE_BOUNDARY_REGEX),
    (m) => m.index
  );
  let searchResultText = "";
  let lastEndOfSentence = 0;
  for (const hitLocation of searchQueryHits) {
    if (hitLocation > lastEndOfSentence) {
      for (let i = 0; i < sentenceBoundaries.length; i++) {
        if (sentenceBoundaries[i] > hitLocation) {
          const startOfSentence = i > 0 ? sentenceBoundaries[i - 1] + 1 : 0;
          const endOfSentence = sentenceBoundaries[i];
          lastEndOfSentence = endOfSentence;
          parsedSentence = pageContent.slice(startOfSentence, endOfSentence).trim();
          searchResultText += `${parsedSentence} ... `;
          break;
        }
      }
    }
    const searchResultWords = tokenize(searchResultText);
    const pageBreakers = searchResultWords.filter((word) => word.length > 50);
    if (pageBreakers.length > 0) {
      searchResultText = fixPageBreakers(searchResultText, pageBreakers);
    }
    if (searchResultWords.length >= MAX_SUMMARY_LENGTH) break;
  }
  result = ellipsize(searchResultText, MAX_SUMMARY_LENGTH).replace(
    searchQueryRegex,
    "<strong>$&</strong>"
  );
  if (!result) {
    result = "[...]";
  }
  return result;
}

function createQueryStringRegex(query) {
  const searchTerms = query.split(" ");
  if (searchTerms.length == 1) {
    return query;
  }
  query = "";
  for (const term of searchTerms) {
    query += `${term}|`;
  }
  query = query.slice(0, -1);
  return `(${query})`;
}

function tokenize(input) {
  const wordMatches = Array.from(input.matchAll(WORD_REGEX), (m) => m);
  return wordMatches.map((m) => ({
    word: m[0],
    start: m.index,
    end: m.index + m[0].length,
    length: m[0].length,
  }));
}

function fixPageBreakers(input, largeWords) {
  largeWords.forEach((word) => {
    const chunked = chunkify(word.word, 20);
    input = input.replace(word.word, chunked);
  });
  return input;
}

function chunkify(input, chunkSize) {
  let output = "";
  let totalChunks = (input.length / chunkSize) | 0;
  let lastChunkIsUneven = input.length % chunkSize > 0;
  if (lastChunkIsUneven) {
    totalChunks += 1;
  }
  for (let i = 0; i < totalChunks; i++) {
    let start = i * chunkSize;
    let end = start + chunkSize;
    if (lastChunkIsUneven && i === totalChunks - 1) {
      end = input.length;
    }
    output += input.slice(start, end) + " ";
  }
  return output;
}

function ellipsize(input, maxLength) {
  const words = tokenize(input);
  if (words.length <= maxLength) {
    return input;
  }
  return input.slice(0, words[maxLength].end) + "...";
}

initSearchIndex();
document.addEventListener("DOMContentLoaded", function() {
  if (document.getElementById("search-form") != null) {
    const searchInput = document.getElementById("search");
    searchInput.addEventListener("keydown", (event) => {
      if (event.keyCode == 13) handleSearchQuery(event);
    });
  }
});

if (!String.prototype.matchAll) {
  String.prototype.matchAll = function(regex) {
    "use strict";

    function ensureFlag(flags, flag) {
      return flags.includes(flag) ? flags : flags + flag;
    }

    function* matchAll(str, regex) {
      const localCopy = new RegExp(regex, ensureFlag(regex.flags, "g"));
      let match;
      while ((match = localCopy.exec(str))) {
        match.index = localCopy.lastIndex - match[0].length;
        yield match;
      }
    }
    return matchAll(this, regex);
  };
}

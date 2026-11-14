const repoForm = document.querySelector("#repo");
const chatForm = document.querySelector("#chat");
const question = document.querySelector("#question");
const history = document.querySelector("#history");
const indexStatus = document.querySelector("#index-status");
const chatStatus = document.querySelector("#chat-status");
let repoId;

async function post(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : "Check the input and try again.");
  }
  return data;
}

function setChatEnabled(enabled) {
  question.disabled = !enabled;
  chatForm.querySelector("button").disabled = !enabled;
}

repoForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = repoForm.querySelector("button");
  button.disabled = true;
  setChatEnabled(false);
  indexStatus.textContent = "Indexing Python files. The first run may download the embedding model.";
  try {
    const data = await post("/ingest", { github_url: document.querySelector("#url").value });
    repoId = data.repo_id;
    history.replaceChildren();
    chatStatus.textContent = "";
    indexStatus.textContent = `Indexed ${data.documents_indexed} Python files at ${data.commit.slice(0, 8)}.`
      + (data.limited ? " Some files exceeded the indexing limits." : "");
  } catch (error) {
    indexStatus.textContent = error.message + (repoId ? " The previously indexed repository is still active." : "");
  } finally {
    button.disabled = false;
    setChatEnabled(Boolean(repoId));
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = question.value.trim();
  if (!text || !repoId) return;
  const indexButton = repoForm.querySelector("button");
  indexButton.disabled = true;
  setChatEnabled(false);
  chatStatus.textContent = "Finding relevant code and generating an answer…";
  try {
    const data = await post("/chat", { repo_id: repoId, question: text });
    const article = document.createElement("article");
    const heading = document.createElement("h3");
    heading.textContent = text;
    const answer = document.createElement("p");
    answer.textContent = data.answer;
    article.append(heading, answer);
    if (data.sources.length) {
      const list = document.createElement("ul");
      for (const source of data.sources) {
        const item = document.createElement("li");
        const link = document.createElement("a");
        link.href = source.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = `[${source.id}] ${source.source} · L${source.start_line}–L${source.end_line}`;
        item.append(link);
        list.append(item);
      }
      article.append(list);
    }
    history.prepend(article);
    question.value = "";
    chatStatus.textContent = "";
  } catch (error) {
    chatStatus.textContent = error.message;
  } finally {
    indexButton.disabled = false;
    setChatEnabled(true);
    question.focus();
  }
});

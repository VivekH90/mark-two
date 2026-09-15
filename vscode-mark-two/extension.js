const vscode = require("vscode");

const DIRECTIVES = [
  "documenttitle", "button", "title", "section", "subsection", "image",
  "enumerate", "itemize", "item", "theorem", "lemma", "definition",
  "corollary", "axiom", "proof", "relatedlinks", "relatedlink"
];

function activate(context) {
  const provider = vscode.languages.registerCompletionItemProvider(
    { language: "mark-two" },
    {
      provideCompletionItems() {
        return DIRECTIVES.map((name) => {
          const item = new vscode.CompletionItem(`@${name}`, vscode.CompletionItemKind.Keyword);
          item.insertText = new vscode.SnippetString(`@${name}{\${1}}`);
          item.detail = "Mark Two directive";
          return item;
        });
      }
    },
    "@"
  );
  context.subscriptions.push(provider);
}

function deactivate() {}

module.exports = { activate, deactivate };

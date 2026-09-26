const vscode = require("vscode");

const DIRECTIVE_SNIPPETS = [
  ["documenttitle", '@documenttitle{${1:Physics}}'],
  ["folder", '@folder{${1:Electromagnetism}}'],
  ["author", '@author{${1:Author}}'],
  ["date", '@date{${1:26 September 2026}}'],
  ["title", '@title{${1:Article Title}}'],
  ["tags", '@tags{${1:topic one}, ${2:topic two}}'],
  ["section", '@section{${1:Section Title}, label = ${2:section-label}}'],
  ["subsection", '@subsection{${1:Subsection Title}, label = ${2:subsection-label}}'],
  ["image", '@image{src = ${1:https://example.com/image.png}, alt = ${2:Description}, caption = ${3:Figure caption}, label = ${4:figure-label}}'],
  ["label", '@label{${1:label-name}}'],
  ["ref", '@ref{${1:label}}'],
  ["relatedlinks", '@relatedlinks{${1:Link name}, href = ${2:https://example.com}}'],
  ["relatedlink", '@relatedlink{${1:Link name}, href = ${2:https://example.com}}'],
  ["bold", '@bold{${1:text}}'],
  ["italic", '@italic{${1:text}}'],
  ["color", '@color{${1:blue}, ${2:text}}'],
  ["button", '@button{${1:Home}, href = ${2:/}, color = ${3:black}}'],
  ["gallery", '@gallery{source = ${1:NASA}, query = ${2:black holes}, count = ${3:7}}'],
];

const ENVIRONMENT_SNIPPETS = [
  ["theorem", '@begin(theorem = ${1:Theorem Title}, label = ${2:theorem-label})\n${0}\n@end(theorem)'],
  ["lemma", '@begin(lemma = ${1:Lemma Title}, label = ${2:lemma-label})\n${0}\n@end(lemma)'],
  ["definition", '@begin(definition = ${1:Definition Title}, label = ${2:definition-label})\n${0}\n@end(definition)'],
  ["corollary", '@begin(corollary = ${1:Corollary Title}, label = ${2:corollary-label})\n${0}\n@end(corollary)'],
  ["axiom", '@begin(axiom = ${1:Axiom Title}, label = ${2:axiom-label})\n${0}\n@end(axiom)'],
  ["proposition", '@begin(proposition = ${1:Proposition Title}, label = ${2:proposition-label})\n${0}\n@end(proposition)'],
  ["remark", '@begin(remark = ${1:Remark Title}, label = ${2:remark-label})\n${0}\n@end(remark)'],
  ["example", '@begin(example = ${1:Example Title}, label = ${2:example-label})\n${0}\n@end(example)'],
  ["conjecture", '@begin(conjecture = ${1:Conjecture Title}, label = ${2:conjecture-label})\n${0}\n@end(conjecture)'],
  ["notation", '@begin(notation = ${1:Notation Title}, label = ${2:notation-label})\n${0}\n@end(notation)'],
  ["warning", '@begin(warning = ${1:Warning Title}, label = ${2:warning-label})\n${0}\n@end(warning)'],
  ["proof", '@begin(proof)\n${0}\n@end(proof)'],
  ["enumerate", '@begin(enumerate)\n@item{${1:First item}}\n@item{${2:Second item}}\n@end(enumerate)'],
  ["itemize", '@begin(itemize)\n@item{${1:First item}}\n@item{${2:Second item}}\n@end(itemize)'],
];

function activate(context) {
  const provider = vscode.languages.registerCompletionItemProvider(
    { language: "mark-two" },
    {
      provideCompletionItems(document, position) {
        const line = document.lineAt(position.line).text.slice(0, position.character);
        const match = line.match(/@([A-Za-z]*)$/);
        if (!match) return undefined;

        const start = position.character - match[0].length;
        const range = new vscode.Range(position.line, start, position.line, position.character);
        const items = [];

        for (const [name, snippet] of DIRECTIVE_SNIPPETS) {
          const item = new vscode.CompletionItem(`@${name}`, vscode.CompletionItemKind.Keyword);
          item.insertText = new vscode.SnippetString(snippet);
          item.filterText = `@${name}`;
          item.detail = "Mark Two directive";
          item.range = range;
          items.push(item);
        }

        for (const [name, snippet] of ENVIRONMENT_SNIPPETS) {
          const item = new vscode.CompletionItem(`@${name}`, vscode.CompletionItemKind.Struct);
          item.insertText = new vscode.SnippetString(snippet);
          item.filterText = `@${name}`;
          item.detail = "Mark Two environment";
          item.range = range;
          items.push(item);
        }

        return items;
      }
    },
    "@"
  );

  context.subscriptions.push(provider);
}

function deactivate() {}

module.exports = { activate, deactivate };

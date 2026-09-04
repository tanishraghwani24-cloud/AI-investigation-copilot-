import { Fragment } from "react";

/**
 * Renders the report's `detailed_narrative` with the structure it already has.
 *
 * The backend emits the narrative as light Markdown — `## Section` headings and
 * `- ` bullets nested by two-space indents. Putting that string in a single
 * <p> let HTML collapse every newline, which is what turned a sectioned report
 * into one unbroken wall of text. This restores the sections rather than
 * inventing any: nothing is added, reordered, or summarised, and a line the
 * parser does not recognise is rendered verbatim as a paragraph.
 *
 * A small dedicated parser is used instead of a Markdown dependency because the
 * narrative only ever uses these three constructs (no emphasis, links or code),
 * and untrusted-HTML rendering is avoided entirely.
 */

interface NarrativeListItem {
  text: string;
  children: NarrativeListItem[];
}

export type NarrativeBlock =
  | { kind: "heading"; text: string }
  | { kind: "paragraph"; text: string }
  | { kind: "list"; items: NarrativeListItem[] };

const HEADING = /^#{1,6}\s+(.*)$/;
const BULLET = /^(\s*)[-*]\s+(.*)$/;
/**
 * "Label: value" lines are common in the narrative ("Finding: ...",
 * "Violation status: ..."). The pattern is deliberately tight — short, starting
 * capitalised, no sentence punctuation — so ordinary prose that happens to
 * contain a colon is not mistaken for a label.
 */
const LABELLED = /^([A-Z][A-Za-z0-9 /()'-]{0,30}):\s+(\S.*)$/;

/** Two spaces of indent per nesting level, as the backend emits it. */
function depthOf(indent: string): number {
  return Math.floor(indent.replace(/\t/g, "  ").length / 2);
}

export function parseNarrative(narrative: string): NarrativeBlock[] {
  const blocks: NarrativeBlock[] = [];
  // Stack of open list levels; index === nesting depth.
  let stack: NarrativeListItem[][] = [];

  const closeList = () => {
    stack = [];
  };

  for (const rawLine of narrative.split("\n")) {
    const line = rawLine.replace(/\s+$/, "");
    if (!line.trim()) {
      closeList();
      continue;
    }

    const heading = HEADING.exec(line.trim());
    if (heading) {
      closeList();
      blocks.push({ kind: "heading", text: heading[1].trim() });
      continue;
    }

    const bullet = BULLET.exec(line);
    if (bullet) {
      const depth = depthOf(bullet[1]);
      const item: NarrativeListItem = { text: bullet[2].trim(), children: [] };

      if (stack.length === 0) {
        const items: NarrativeListItem[] = [item];
        blocks.push({ kind: "list", items });
        stack = [items];
        continue;
      }

      // Clamp: a jump deeper than one level still nests exactly one level,
      // so malformed indentation cannot drop the item.
      const level = Math.min(depth, stack.length - 1);
      stack = stack.slice(0, level + 1);
      const siblings = stack[level];

      if (depth > level && siblings.length > 0) {
        const parent = siblings[siblings.length - 1];
        parent.children.push(item);
        stack.push(parent.children);
      } else {
        siblings.push(item);
      }
      continue;
    }

    closeList();
    blocks.push({ kind: "paragraph", text: line.trim() });
  }

  return blocks;
}

function ItemText({ text }: { text: string }) {
  const labelled = LABELLED.exec(text);
  if (!labelled) return <>{text}</>;
  return (
    <>
      <span className="font-medium text-gray-800 dark:text-gray-100">{labelled[1]}:</span>{" "}
      {labelled[2]}
    </>
  );
}

function NarrativeList({ items, depth = 0 }: { items: NarrativeListItem[]; depth?: number }) {
  return (
    <ul
      className={
        depth === 0
          ? "list-disc space-y-1.5 pl-5 text-sm text-gray-600 marker:text-gray-400 dark:text-gray-300"
          : "mt-1.5 list-[circle] space-y-1 pl-5 text-sm text-gray-600 marker:text-gray-300 dark:text-gray-300"
      }
    >
      {items.map((item, index) => (
        <li key={`${depth}-${index}-${item.text.slice(0, 32)}`}>
          <ItemText text={item.text} />
          {item.children.length > 0 && (
            <NarrativeList items={item.children} depth={depth + 1} />
          )}
        </li>
      ))}
    </ul>
  );
}

export function StructuredNarrative({ narrative }: { narrative: string }) {
  const blocks = parseNarrative(narrative);

  return (
    <div className="space-y-4" data-testid="structured-narrative">
      {blocks.map((block, index) => {
        const key = `${block.kind}-${index}`;
        if (block.kind === "heading") {
          return (
            <h5
              key={key}
              className="border-t border-gray-100 pt-4 text-xs font-semibold uppercase tracking-wider text-gray-500 first:border-t-0 first:pt-0 dark:border-gray-800 dark:text-gray-400"
            >
              {block.text}
            </h5>
          );
        }
        if (block.kind === "list") {
          return (
            <Fragment key={key}>
              <NarrativeList items={block.items} />
            </Fragment>
          );
        }
        return (
          <p key={key} className="text-sm leading-relaxed text-gray-600 dark:text-gray-300">
            {block.text}
          </p>
        );
      })}
    </div>
  );
}

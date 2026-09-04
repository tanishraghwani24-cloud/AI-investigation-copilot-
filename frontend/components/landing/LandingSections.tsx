import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import {
  AlertTriangle,
  ArrowRight,
  ArrowUpNarrowWide,
  Building2,
  FileBarChart,
  FolderSearch,
  Gauge,
  Gavel,
  Globe2,
  Inbox,
  KeyRound,
  Lock,
  RefreshCcw,
  ScrollText,
  Search,
  ShieldAlert,
  Sparkles,
  UsersRound,
} from "lucide-react";

/**
 * Landing-page storytelling below the hero. Purely presentational content —
 * no data fetching, no routing besides the existing "/officer" destination,
 * no change to app functionality. Reuses the same dark: token pairs and
 * severity colors (red/amber) already established in OfficerDashboard.
 */

function SectionKicker({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
      {children}
    </p>
  );
}

function SectionHeading({
  kicker,
  title,
  subtitle,
}: {
  kicker: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="relative mx-auto max-w-2xl text-center">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-0 -z-10 h-40 w-80 -translate-x-1/2 -translate-y-1/2 rounded-full bg-blue-500/10 blur-3xl dark:bg-blue-500/20"
      />
      <SectionKicker>{kicker}</SectionKicker>
      <h2 className="mt-2 text-2xl font-extrabold tracking-tight text-gray-900 sm:text-3xl dark:text-white">
        {title}
      </h2>
      {subtitle ? (
        <p className="mt-3 text-sm text-gray-600 sm:text-base dark:text-gray-400">
          {subtitle}
        </p>
      ) : null}
    </div>
  );
}

function Card({
  icon: Icon,
  title,
  description,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition-colors hover:border-blue-300 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-blue-800">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400">
        <Icon className="h-5 w-5" strokeWidth={2} />
      </div>
      <h3 className="mt-4 text-sm font-semibold text-gray-900 dark:text-white">{title}</h3>
      <p className="mt-1.5 text-sm leading-relaxed text-gray-600 dark:text-gray-400">
        {description}
      </p>
    </div>
  );
}

const WORKFLOW_STEPS: { icon: LucideIcon; title: string; description: string }[] = [
  {
    icon: AlertTriangle,
    title: "Risk Signal",
    description: "A suspicious transaction, activity pattern, or alert enters the workflow.",
  },
  {
    icon: ArrowUpNarrowWide,
    title: "Prioritize",
    description: "Risk information surfaces the higher-risk work first.",
  },
  {
    icon: Search,
    title: "Investigate",
    description: "Review transaction activity, customer context, and evidence together.",
  },
  {
    icon: UsersRound,
    title: "Collaborate",
    description: "See who owns the case and what the team is working on now.",
  },
  {
    icon: Gavel,
    title: "Decide",
    description: "Reach a structured outcome, informed by context — not a score alone.",
  },
  {
    icon: ScrollText,
    title: "Audit",
    description: "Every important action is preserved in a traceable history.",
  },
];

const CAPABILITIES: { icon: LucideIcon; title: string; description: string }[] = [
  {
    icon: Inbox,
    title: "Officer Inbox",
    description: "The operational starting point — prioritized alerts that need investigator attention.",
  },
  {
    icon: FolderSearch,
    title: "Investigation Workspace",
    description: "A structured place to review a case: transactions, context, evidence, and history.",
  },
  {
    icon: ShieldAlert,
    title: "Risk Prioritization",
    description: "Severity-first ordering keeps the highest-risk work in front of investigators.",
  },
  {
    icon: UsersRound,
    title: "Collaborative Activity",
    description: "Ownership and live activity, so work is never duplicated across a team.",
  },
  {
    icon: Sparkles,
    title: "Decision Intelligence",
    description: "Connects risk context to the investigation decision, not just a number.",
  },
  {
    icon: FileBarChart,
    title: "Reports",
    description: "Investigation outcomes and operational visibility for the wider organization.",
  },
  {
    icon: ScrollText,
    title: "Audit Trail",
    description: "A platform-wide, chronological record that supports accountability.",
  },
];

const SECURITY_CONTROLS: { icon: LucideIcon; title: string; description: string }[] = [
  {
    icon: Lock,
    title: "API Authentication",
    description: "Protected endpoints only respond to requests carrying a valid credential.",
  },
  {
    icon: Gauge,
    title: "Rate Limiting",
    description: "Excessive request frequency from a single client is throttled, not tolerated.",
  },
  {
    icon: Globe2,
    title: "Restricted CORS",
    description: "Browser requests are accepted only from trusted, explicitly configured origins.",
  },
  {
    icon: KeyRound,
    title: "Server-Side Secrets",
    description: "Credentials stay on the server — never shipped inside frontend code.",
  },
  {
    icon: RefreshCcw,
    title: "Credential Rotation",
    description: "A leaked or retiring credential can be replaced without downtime.",
  },
  {
    icon: ScrollText,
    title: "Platform Audit Log",
    description: "Actor, action, target, and timestamp — traceable across the whole platform.",
  },
];

function OverviewSection() {
  return (
    <section className="py-16 sm:py-24">
      <div className="mx-auto max-w-3xl px-4 text-center">
        <SectionKicker>ARIA · Autonomous Risk Investigation Agent</SectionKicker>
        <h2 className="mt-2 text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl dark:text-white">
          From Risk Signal to Defensible Decision.
        </h2>
        <p className="mt-4 text-base leading-relaxed text-gray-600 sm:text-lg dark:text-gray-400">
          ARIA brings risk signals, investigation context, investigator activity, decisions,
          and audit history into one structured workflow — an investigation operating layer,
          not another fraud dashboard.
        </p>
      </div>
    </section>
  );
}

function WorkflowSection() {
  return (
    <section className="-mx-4 bg-gray-50 px-4 py-16 sm:-mx-6 sm:px-6 sm:py-24 dark:bg-gray-900/40">
      <SectionHeading
        kicker="How ARIA Works"
        title="One workflow, from signal to accountability."
        subtitle="Every investigation moves through the same structured sequence."
      />
      <div className="mx-auto mt-12 grid max-w-6xl grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-6">
        {WORKFLOW_STEPS.map((step, index) => (
          <div
            key={step.title}
            className="relative rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900"
          >
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">
                {String(index + 1).padStart(2, "0")}
              </span>
              <step.icon className="h-4 w-4 text-blue-600 dark:text-blue-400" strokeWidth={2} />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-gray-900 dark:text-white">
              {step.title}
            </h3>
            <p className="mt-1.5 text-xs leading-relaxed text-gray-600 dark:text-gray-400">
              {step.description}
            </p>
            {index < WORKFLOW_STEPS.length - 1 ? (
              <ArrowRight
                aria-hidden="true"
                className="absolute -right-3 top-1/2 hidden h-4 w-4 -translate-y-1/2 text-gray-300 lg:block dark:text-gray-700"
              />
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}

function CapabilitiesSection() {
  return (
    <section className="py-16 sm:py-24">
      <SectionHeading
        kicker="Core Capabilities"
        title="Built around the investigation, not just the alert."
      />
      <div className="mx-auto mt-12 grid max-w-6xl grid-cols-1 gap-4 px-4 sm:grid-cols-2 lg:grid-cols-3">
        {CAPABILITIES.map((item) => (
          <Card key={item.title} {...item} />
        ))}
      </div>
    </section>
  );
}

function CollaborationSection() {
  return (
    <section className="-mx-4 bg-gray-50 px-4 py-16 sm:-mx-6 sm:px-6 sm:py-24 dark:bg-gray-900/40">
      <SectionHeading
        kicker="Collaborative Investigations"
        title="Know who is working on what."
        subtitle="Investigation ownership and current activity, visible across the team — not isolated investigator screens."
      />
      <div className="mx-auto mt-12 grid max-w-4xl grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">CASE-A104</span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:ring-emerald-800">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Reviewing now
            </span>
          </div>
          <p className="mt-3 text-sm font-medium text-gray-900 dark:text-white">
            Owned by Investigator A
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Currently examining transaction context and evidence.
          </p>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">CASE-B217</span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 ring-1 ring-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:ring-gray-700">
              <span className="h-1.5 w-1.5 rounded-full bg-gray-400" />
              Assigned
            </span>
          </div>
          <p className="mt-3 text-sm font-medium text-gray-900 dark:text-white">
            Owned by Investigator B
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            A separate case, worked independently in parallel.
          </p>
        </div>
      </div>
      <ul className="mx-auto mt-8 grid max-w-4xl grid-cols-1 gap-3 sm:grid-cols-3">
        {[
          "Clear ownership for every investigation",
          "Live activity, not just a historical log",
          "No duplicated work, easier handoffs",
        ].map((line) => (
          <li
            key={line}
            className="rounded-xl border border-gray-200 bg-white px-4 py-3 text-center text-xs font-medium text-gray-700 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300"
          >
            {line}
          </li>
        ))}
      </ul>
    </section>
  );
}

function DecisionIntelligenceSection() {
  return (
    <section className="py-16 sm:py-24">
      <div className="mx-auto grid max-w-5xl grid-cols-1 gap-10 px-4 sm:grid-cols-2 sm:items-center">
        <div>
          <SectionKicker>Decision Intelligence</SectionKicker>
          <h2 className="mt-2 text-2xl font-extrabold tracking-tight text-gray-900 sm:text-3xl dark:text-white">
            Beyond a risk score.
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-gray-600 sm:text-base dark:text-gray-400">
            A number alone does not explain an investigation. ARIA connects risk context,
            evidence, and investigator actions — moving from &ldquo;something looks
            suspicious&rdquo; to a structured, defensible decision, with a human investigator
            still at the center of it.
          </p>
        </div>
        <ul className="space-y-3">
          {[
            "Risk information helps prioritize cases",
            "Investigation context explains what is happening",
            "Evidence and transaction context support the case",
            "The final outcome remains traceable",
          ].map((line) => (
            <li
              key={line}
              className="flex items-start gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300"
            >
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />
              {line}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function SecuritySection() {
  return (
    <section className="-mx-4 bg-gray-50 px-4 py-16 sm:-mx-6 sm:px-6 sm:py-24 dark:bg-gray-900/40">
      <SectionHeading
        kicker="Security & Trust"
        title="Protected by design. Traceable by default."
      />
      <div className="mx-auto mt-12 grid max-w-5xl grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SECURITY_CONTROLS.map((item) => (
          <Card key={item.title} {...item} />
        ))}
      </div>
      <p className="mx-auto mt-8 max-w-2xl rounded-xl border border-blue-200 bg-blue-50 px-5 py-4 text-center text-sm text-blue-900 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-200">
        Authentication, rate limiting, and restricted origins guard the API boundary. Secrets
        stay server-side, credentials can rotate, and the platform audit log keeps every
        important action traceable.
      </p>
    </section>
  );
}

function CrossBankSection() {
  return (
    <section className="py-16 sm:py-24">
      <SectionHeading
        kicker="Cross-Bank Investigations"
        title="Sender and receiver don't always share a bank."
        subtitle="ARIA works from the data legitimately available to the investigating institution — it does not assume privileged access to another bank's internal systems."
      />
      <div className="mx-auto mt-12 flex max-w-3xl flex-col items-center gap-4 px-4 sm:flex-row sm:justify-center">
        <div className="flex w-full flex-col items-center gap-2 rounded-2xl border border-blue-200 bg-blue-50 px-6 py-5 text-center sm:w-56 dark:border-blue-900 dark:bg-blue-950/40">
          <Building2 className="h-6 w-6 text-blue-600 dark:text-blue-400" strokeWidth={2} />
          <p className="text-sm font-semibold text-gray-900 dark:text-white">
            Investigating Institution
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400">Full context available</p>
        </div>
        <ArrowRight
          aria-hidden="true"
          className="h-5 w-5 shrink-0 rotate-90 text-gray-400 sm:rotate-0 dark:text-gray-600"
        />
        <div className="flex w-full flex-col items-center gap-2 rounded-2xl border border-dashed border-gray-300 bg-white px-6 py-5 text-center sm:w-56 dark:border-gray-700 dark:bg-gray-900">
          <Building2 className="h-6 w-6 text-gray-400 dark:text-gray-500" strokeWidth={2} />
          <p className="text-sm font-semibold text-gray-900 dark:text-white">
            External Counterparty
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400">Not directly integrated</p>
        </div>
      </div>
      <p className="mx-auto mt-6 max-w-xl px-4 text-center text-xs text-gray-500 dark:text-gray-500">
        The investigation still proceeds using information available on the investigating side,
        with external-counterparty context represented — not fabricated.
      </p>
    </section>
  );
}

function ReportsSection() {
  return (
    <section className="-mx-4 bg-gray-50 px-4 py-16 sm:-mx-6 sm:px-6 sm:py-24 dark:bg-gray-900/40">
      <SectionHeading
        kicker="Reports"
        title="From individual cases to organizational visibility."
        subtitle="A natural transition from investigator work to management-level intelligence."
      />
      <ul className="mx-auto mt-10 grid max-w-3xl grid-cols-1 gap-3 sm:grid-cols-2">
        {[
          "Investigation outcomes",
          "Operational investigation visibility",
          "Risk trend concepts",
          "Management-level activity visibility",
        ].map((line) => (
          <li
            key={line}
            className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300"
          >
            <FileBarChart className="h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400" strokeWidth={2} />
            {line}
          </li>
        ))}
      </ul>
    </section>
  );
}

function ClosingCtaSection() {
  return (
    <section className="py-16 sm:py-24">
      <div className="relative mx-auto max-w-2xl overflow-hidden rounded-3xl border border-gray-200 bg-white px-6 py-12 text-center dark:border-gray-800 dark:bg-gray-900">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute left-1/2 top-0 h-40 w-80 -translate-x-1/2 -translate-y-1/2 rounded-full bg-blue-500/10 blur-3xl dark:bg-blue-500/20"
        />
        <h2 className="text-2xl font-extrabold tracking-tight text-gray-900 sm:text-3xl dark:text-white">
          Investigate smarter. Collaborate faster.
        </h2>
        <p className="mt-3 text-sm text-gray-600 sm:text-base dark:text-gray-400">
          Keep every decision traceable, from the first risk signal to the final outcome.
        </p>
        <Link
          href="/officer"
          className="mt-6 inline-block rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition-colors hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-400"
        >
          Go to Officer Inbox
        </Link>
      </div>
    </section>
  );
}

export default function LandingSections() {
  return (
    <div className="w-full text-left">
      <OverviewSection />
      <WorkflowSection />
      <CapabilitiesSection />
      <CollaborationSection />
      <DecisionIntelligenceSection />
      <SecuritySection />
      <CrossBankSection />
      <ReportsSection />
      <ClosingCtaSection />
    </div>
  );
}

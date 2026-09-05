"use client";

import { useRef } from "react";
import type { LucideIcon } from "lucide-react";
import { motion, useScroll, useTransform, type MotionProps } from "motion/react";
import GlassmorphismCta from "@/components/ui/GlassmorphismCta";
import { ContainerScroll, CardSticky } from "@/components/ui/cards-stack";
import {
  Reveal,
  WordsReveal,
  blurIn,
  revealFrom,
  revealUp,
  scaleIn,
  stagger,
  wipeIn,
} from "@/components/landing/ScrollReveal";
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
    <motion.p
      className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400"
      {...wipeIn()}
    >
      {children}
    </motion.p>
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
      <SectionKicker>{kicker}</SectionKicker>
      <motion.h2
        className="mt-2 text-2xl font-extrabold tracking-tight text-gray-900 sm:text-3xl dark:text-white"
        {...blurIn(0.06)}
      >
        {title}
      </motion.h2>
      {subtitle ? (
        <motion.p
          className="mt-3 text-sm text-gray-600 sm:text-base dark:text-gray-400"
          {...revealUp(0.14)}
        >
          {subtitle}
        </motion.p>
      ) : null}
    </div>
  );
}

function Card({
  icon: Icon,
  title,
  description,
  ...motionProps
}: {
  icon: LucideIcon;
  title: string;
  description: string;
} & MotionProps) {
  return (
    <motion.div
      className="landing-card rounded-2xl border border-zinc-200 bg-white p-5 dark:border-white/10 dark:bg-zinc-950"
      whileHover={{ y: -12, scale: 1.02, rotateX: 5, rotateY: -4, transition: { duration: 0.34, ease: "easeOut" } }}
      {...motionProps}
    >
      <div className="landing-card-icon flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-900 text-white shadow-lg shadow-black/15 dark:bg-white dark:text-zinc-950 dark:shadow-white/10">
        <Icon className="h-5 w-5" strokeWidth={2} />
      </div>
      <h3 className="mt-4 text-sm font-semibold text-gray-900 dark:text-white">{title}</h3>
      <p className="mt-1.5 text-sm leading-relaxed text-gray-600 dark:text-gray-400">
        {description}
      </p>
    </motion.div>
  );
}

const WORKFLOW_STEPS: { icon: LucideIcon; title: string; description: string }[] = [
  {
    icon: AlertTriangle,
    title: "Risk Signal",
    description:
      "ARIA begins by identifying suspicious activity from transaction patterns, alerts, and risk signals entering the investigation workflow. Instead of treating every alert equally, the platform brings relevant transaction and contextual information together so investigators can understand what triggered attention and why the activity may require review.",
  },
  {
    icon: ArrowUpNarrowWide,
    title: "Prioritize",
    description:
      "ARIA helps investigators focus their attention on the cases that matter most. Risk information and investigation context are used to surface higher-risk work first, reducing the time spent manually sorting through large volumes of alerts and helping investigators concentrate on potentially significant financial-crime activity.",
  },
  {
    icon: Search,
    title: "Investigate",
    description:
      "Investigators can examine transaction activity alongside customer context and available evidence within a structured investigation workflow. ARIA brings these pieces together so the investigator can move beyond a simple risk score and build a clearer understanding of the activity, relationships, and circumstances surrounding the case.",
  },
  {
    icon: UsersRound,
    title: "Collaborate",
    description:
      "Investigations are not isolated to one investigator. ARIA provides visibility into investigation ownership and team activity, helping investigators understand who is handling a case and what work is currently in progress. This reduces duplicated effort, improves handoffs, and creates a more coordinated investigation process.",
  },
  {
    icon: Gavel,
    title: "Decide",
    description:
      "ARIA supports investigators in reaching structured investigation outcomes using the full context of the case rather than relying on a score alone. Transaction information, evidence, risk signals, and investigation activity can be considered together, helping produce decisions that are clearer, more consistent, and easier to understand.",
  },
  {
    icon: ScrollText,
    title: "Audit",
    description:
      "Every important investigation action can become part of a traceable history. ARIA's auditability provides visibility into who performed an action, what changed, and when it happened, creating an accountable investigation trail that can help reconstruct the journey from the initial risk signal to the final decision.",
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
        <motion.h2
          className="mt-2 text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl dark:text-white"
          {...blurIn(0.06)}
        >
          From Risk Signal to Defensible Decision.
        </motion.h2>
        <WordsReveal
          className="mt-4 text-base leading-relaxed text-gray-600 sm:text-lg dark:text-gray-400"
          delay={0.16}
          text="ARIA brings risk signals, investigation context, investigator activity, decisions, and audit history into one structured workflow — an investigation operating layer, not another fraud dashboard."
        />
      </div>
    </section>
  );
}

function WorkflowCard({
  step,
  index,
}: {
  step: (typeof WORKFLOW_STEPS)[number];
  index: number;
}) {
  const slotRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: slotRef,
    offset: ["start start", "end start"],
  });
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.96]);
  const opacity = useTransform(scrollYProgress, [0, 1], [1, 0.82]);

  return (
    <div ref={slotRef} className="relative min-h-[40vh] pb-6 sm:pb-8">
      <CardSticky
        index={index}
        topOffset={112}
        incrementY={0}
        incrementZ={10}
        className="workflow-case-card landing-card min-h-[19rem] rounded-3xl p-7 sm:min-h-[18rem] sm:p-9"
        style={{ scale, opacity }}
        whileHover={{ y: -6, scale: 1.01, rotateX: 2, rotateY: -1, transition: { duration: 0.28, ease: "easeOut" } }}
        {...revealUp(stagger(index))}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <span className="text-3xl font-bold tabular-nums text-violet-600/90 dark:text-violet-400/90">
              {String(index + 1).padStart(2, "0")}
            </span>
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-violet-500/20 bg-violet-500/[0.06] text-violet-600 dark:border-violet-400/25 dark:bg-violet-400/10 dark:text-violet-300">
              <step.icon className="h-5 w-5" strokeWidth={2} />
            </span>
          </div>
          <span className="hidden shrink-0 text-right text-[10px] font-semibold uppercase leading-relaxed tracking-[0.18em] text-gray-400 dark:text-gray-500 sm:block">
            Investigation Stage
            <br />
            {String(index + 1).padStart(2, "0")} / {String(WORKFLOW_STEPS.length).padStart(2, "0")}
          </span>
        </div>
        <h3 className="mt-7 text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
          {step.title}
        </h3>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-gray-700 sm:text-base dark:text-gray-300">
          {step.description}
        </p>
      </CardSticky>
    </div>
  );
}

function WorkflowSection() {
  return (
    <section className="-mx-4 bg-zinc-50 px-4 py-16 sm:-mx-6 sm:px-6 sm:py-24 dark:bg-white/[0.02]">
      <div className="mx-auto max-w-6xl">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)] lg:gap-16">
          <div className="lg:sticky lg:top-28 lg:flex lg:min-h-[60vh] lg:flex-col lg:justify-center">
            <SectionKicker>How ARIA Works</SectionKicker>
            <motion.h2
              className="mt-3 max-w-sm text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl dark:text-white"
              {...blurIn(0.06)}
            >
              One workflow, from signal to accountability.
            </motion.h2>
            <motion.p
              className="mt-4 max-w-sm text-sm leading-relaxed text-gray-600 sm:text-base dark:text-gray-400"
              {...revealUp(0.14)}
            >
              Every investigation moves through the same structured sequence.
            </motion.p>
            <motion.span
              className="mt-8 inline-flex w-fit items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/[0.06] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-violet-700/80 dark:border-violet-400/20 dark:bg-violet-400/[0.08] dark:text-violet-300/80"
              {...wipeIn(0.22)}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-violet-500 dark:bg-violet-400" />
              ARIA Workflow
            </motion.span>
          </div>

          <ContainerScroll>
            {WORKFLOW_STEPS.map((step, index) => (
              <WorkflowCard key={step.title} step={step} index={index} />
            ))}
          </ContainerScroll>
        </div>
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
      <div className="landing-card-grid mx-auto mt-12 grid max-w-6xl grid-cols-1 gap-4 px-4 sm:grid-cols-2 lg:grid-cols-3">
        {CAPABILITIES.map((item, index) => (
          <Card key={item.title} {...item} {...scaleIn(stagger(index))} />
        ))}
      </div>
    </section>
  );
}

function CollaborationSection() {
  return (
    <section className="-mx-4 bg-zinc-50 px-4 py-16 sm:-mx-6 sm:px-6 sm:py-24 dark:bg-white/[0.02]">
      <SectionHeading
        kicker="Collaborative Investigations"
        title="Know who is working on what."
        subtitle="Investigation ownership and current activity, visible across the team — not isolated investigator screens."
      />
      <div className="mx-auto mt-12 grid max-w-4xl grid-cols-1 gap-4 sm:grid-cols-2">
        <motion.div
          className="landing-card rounded-2xl border border-zinc-200 bg-white p-5 dark:border-white/10 dark:bg-zinc-950"
          whileHover={{ y: -8, rotateX: 2, rotateY: -2, transition: { duration: 0.32, ease: "easeOut" } }}
          {...revealFrom("left")}
        >
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
        </motion.div>
        <motion.div
          className="landing-card rounded-2xl border border-zinc-200 bg-white p-5 dark:border-white/10 dark:bg-zinc-950"
          whileHover={{ y: -8, rotateX: 2, rotateY: 2, transition: { duration: 0.32, ease: "easeOut" } }}
          {...revealFrom("right", 0.08)}
        >
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
        </motion.div>
      </div>
      <ul className="mx-auto mt-8 grid max-w-4xl grid-cols-1 gap-3 sm:grid-cols-3">
        {[
          "Clear ownership for every investigation",
          "Live activity, not just a historical log",
          "No duplicated work, easier handoffs",
        ].map((line, index) => (
          <motion.li
            key={line}
            className="landing-card rounded-xl border border-zinc-200 bg-white px-4 py-3 text-center text-xs font-medium text-gray-700 dark:border-white/10 dark:bg-zinc-950 dark:text-gray-300"
            whileHover={{ y: -5, rotateX: 1, transition: { duration: 0.3, ease: "easeOut" } }}
            {...wipeIn(stagger(index))}
          >
            {line}
          </motion.li>
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
          <motion.h2
            className="mt-2 text-2xl font-extrabold tracking-tight text-gray-900 sm:text-3xl dark:text-white"
            {...blurIn(0.06)}
          >
            Beyond a risk score.
          </motion.h2>
          <WordsReveal
            className="mt-4 text-sm leading-relaxed text-gray-600 sm:text-base dark:text-gray-400"
            delay={0.16}
            text="A number alone does not explain an investigation. ARIA connects risk context, evidence, and investigator actions — moving from “something looks suspicious” to a structured, defensible decision, with a human investigator still at the center of it."
          />
        </div>
        <ul className="space-y-3">
          {[
            "Risk information helps prioritize cases",
            "Investigation context explains what is happening",
            "Evidence and transaction context support the case",
            "The final outcome remains traceable",
          ].map((line, index) => (
            <motion.li
              key={line}
              className="landing-card flex items-start gap-3 rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm text-gray-700 dark:border-white/10 dark:bg-zinc-950 dark:text-gray-300"
              whileHover={{ x: 6, y: -3, rotateX: 1, transition: { duration: 0.3, ease: "easeOut" } }}
              {...revealFrom("right", stagger(index))}
            >
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-zinc-900 dark:bg-white" />
              {line}
            </motion.li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function SecuritySection() {
  return (
    <section className="-mx-4 bg-zinc-50 px-4 py-16 sm:-mx-6 sm:px-6 sm:py-24 dark:bg-white/[0.02]">
      <SectionHeading
        kicker="Security & Trust"
        title="Protected by design. Traceable by default."
      />
      <div className="mx-auto mt-12 grid max-w-5xl grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SECURITY_CONTROLS.map((item, index) => (
          <Card key={item.title} {...item} {...revealUp(stagger(index))} />
        ))}
      </div>
      <motion.p
        className="landing-card mx-auto mt-8 max-w-2xl rounded-xl border border-zinc-200 bg-white px-5 py-4 text-center text-sm text-zinc-900 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-200"
        whileHover={{ y: -5, rotateX: 1, transition: { duration: 0.3, ease: "easeOut" } }}
        {...scaleIn()}
      >
        Authentication, rate limiting, and restricted origins guard the API boundary. Secrets
        stay server-side, credentials can rotate, and the platform audit log keeps every
        important action traceable.
      </motion.p>
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
        <motion.div
          className="landing-card flex w-full flex-col items-center gap-2 rounded-2xl border border-zinc-200 bg-white px-6 py-5 text-center sm:w-56 dark:border-white/10 dark:bg-zinc-950"
          whileHover={{ y: -7, rotateX: 2, rotateY: -2, transition: { duration: 0.32, ease: "easeOut" } }}
          {...scaleIn()}
        >
          <Building2 className="h-6 w-6 text-zinc-800 dark:text-zinc-200" strokeWidth={2} />
          <p className="text-sm font-semibold text-gray-900 dark:text-white">
            Investigating Institution
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400">Full context available</p>
        </motion.div>
        <ArrowRight
          aria-hidden="true"
          className="h-5 w-5 shrink-0 rotate-90 text-gray-400 sm:rotate-0 dark:text-gray-600"
        />
        <motion.div
          className="landing-card flex w-full flex-col items-center gap-2 rounded-2xl border border-dashed border-zinc-300 bg-white px-6 py-5 text-center sm:w-56 dark:border-white/15 dark:bg-zinc-950"
          whileHover={{ y: -7, rotateX: 2, rotateY: 2, transition: { duration: 0.32, ease: "easeOut" } }}
          {...scaleIn(0.12)}
        >
          <Building2 className="h-6 w-6 text-gray-400 dark:text-gray-500" strokeWidth={2} />
          <p className="text-sm font-semibold text-gray-900 dark:text-white">
            External Counterparty
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400">Not directly integrated</p>
        </motion.div>
      </div>
      <motion.p
        className="mx-auto mt-6 max-w-xl px-4 text-center text-xs text-gray-500 dark:text-gray-500"
        {...revealUp(0.05)}
      >
        The investigation still proceeds using information available on the investigating side,
        with external-counterparty context represented — not fabricated.
      </motion.p>
    </section>
  );
}

function ReportsSection() {
  return (
    <section className="-mx-4 bg-zinc-50 px-4 py-16 sm:-mx-6 sm:px-6 sm:py-24 dark:bg-white/[0.02]">
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
        ].map((line, index) => (
          <motion.li
            key={line}
            className="landing-card flex items-center gap-3 rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm text-gray-700 dark:border-white/10 dark:bg-zinc-950 dark:text-gray-300"
            whileHover={{ x: 6, y: -3, rotateX: 1, transition: { duration: 0.3, ease: "easeOut" } }}
            {...revealUp(stagger(index))}
          >
            <FileBarChart className="h-4 w-4 shrink-0 text-zinc-800 dark:text-zinc-200" strokeWidth={2} />
            {line}
          </motion.li>
        ))}
      </ul>
    </section>
  );
}

function ClosingCtaSection() {
  return (
    <section className="py-16 sm:py-24">
      <div className="landing-card relative mx-auto max-w-2xl overflow-hidden rounded-3xl border border-zinc-200 bg-white px-6 py-12 text-center dark:border-white/10 dark:bg-zinc-950">
        <motion.h2
          className="text-2xl font-extrabold tracking-tight text-gray-900 sm:text-3xl dark:text-white"
          {...blurIn()}
        >
          Investigate smarter. Collaborate faster.
        </motion.h2>
        <motion.p
          className="mt-3 text-sm text-gray-600 sm:text-base dark:text-gray-400"
          {...revealUp(0.1)}
        >
          Keep every decision traceable, from the first risk signal to the final outcome.
        </motion.p>
        <Reveal variant="scale" delay={0.2}>
          <GlassmorphismCta
            href="/officer"
            label="Go to Officer Inbox"
            className="mt-6"
          />
        </Reveal>
      </div>
    </section>
  );
}

export default function LandingSections() {
  return (
    <div className="landing-shell relative isolate w-full overflow-x-clip text-left">
      <div aria-hidden="true" className="landing-blue-dot landing-blue-dot-one" />
      <div aria-hidden="true" className="landing-blue-dot landing-blue-dot-two" />
      <div aria-hidden="true" className="landing-blue-dot landing-blue-dot-three" />
      <div className="relative z-10">
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
    </div>
  );
}

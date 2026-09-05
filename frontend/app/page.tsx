import MagnifyLens from "@/components/MagnifyLens";
import MagicRings from "@/components/ui/MagicRings";
import LandingSections from "@/components/landing/LandingSections";
import GlassmorphismCta from "@/components/ui/GlassmorphismCta";
import { Reveal } from "@/components/landing/ScrollReveal";
import { Footer } from "@/components/layout/Footer";

/**
 * Marks the document as able to run the scroll reveals, which lets the
 * `.reveal-ready [data-reveal]` rule in globals.css hide them from the very
 * first paint instead of letting the prerendered text flash in before Motion
 * mounts. Inline and above the sections so it runs while the HTML below is
 * still being parsed; if scripting is off the class is never added and every
 * reveal simply stays visible.
 */
const REVEAL_INIT_SCRIPT = `document.documentElement.classList.add('reveal-ready');`;

export default function Home() {
  return (
    <div className="w-full">
      <script dangerouslySetInnerHTML={{ __html: REVEAL_INIT_SCRIPT }} />
      <div className="relative flex w-full flex-col items-center justify-center min-h-[60vh] overflow-hidden px-2 text-center">
        {/*
          Decorative background layer. `hidden sm:block` keeps it off the
          smallest phones (a WebGL canvas is unnecessary weight there and this
          is purely visual), `pointer-events-none` guarantees it never steals
          clicks from the button below, and the opacity is toned down further
          in light mode where these saturated colors read as harsh on a white
          background.
        */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 z-0 hidden opacity-25 sm:block dark:opacity-50"
        >
          <MagicRings
            color="#a855f7"
            colorTwo="#6366f1"
            ringCount={6}
            speed={1}
            attenuation={10}
            lineThickness={2}
            baseRadius={0.35}
            radiusStep={0.1}
            scaleRate={0.1}
            opacity={1}
            blur={0}
            noiseAmount={0.1}
            rotation={0}
            ringGap={1.5}
            fadeIn={0.7}
            fadeOut={0.5}
            followMouse={false}
            mouseInfluence={0.2}
            hoverScale={1.2}
            parallax={0.05}
            clickBurst={false}
          />
        </div>

        <div className="relative z-10 flex flex-col items-center">
          <MagnifyLens />
          <Reveal
            as="p"
            variant="up"
            className="text-base sm:text-lg text-gray-600 mb-8 max-w-2xl dark:text-gray-300"
          >
            Fraud Investigation & Decision Intelligence Platform
          </Reveal>
          <Reveal variant="scale" delay={0.18}>
            <GlassmorphismCta href="/officer" label="Go to Officer Inbox" />
          </Reveal>
        </div>
      </div>

      <LandingSections />
      <Footer />
    </div>
  );
}

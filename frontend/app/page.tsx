import Link from "next/link";
import MagnifyLens from "@/components/MagnifyLens";
import MagicRings from "@/components/ui/MagicRings";
import LandingSections from "@/components/landing/LandingSections";

export default function Home() {
  return (
    <div className="w-full">
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
          <p className="text-base sm:text-lg text-gray-600 mb-8 max-w-2xl dark:text-gray-300">
            Fraud Investigation & Decision Intelligence Platform
          </p>
          <Link
            href="/officer"
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors dark:bg-blue-500 dark:hover:bg-blue-400"
          >
            Go to Officer Inbox
          </Link>
        </div>
      </div>

      <LandingSections />
    </div>
  );
}

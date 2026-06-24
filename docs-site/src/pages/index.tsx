import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';

type LoopStep = {
  num: number;
  label: string;
  blurb: string;
  /** Position of the node center on the wheel, in percent. */
  top: string;
  left: string;
};

// Five steps placed evenly around a circle (72° apart), starting at the top
// and flowing clockwise. Positions are pre-computed for a radius of 38% on a
// square wheel centered at 50%,50%.
const LOOP_STEPS: LoopStep[] = [
  {
    num: 1,
    label: 'Pour in your data',
    blurb: 'Records, symptoms, medicines, lifestyle. The more it knows, the sharper it gets.',
    top: '12%',
    left: '50%',
  },
  {
    num: 2,
    label: "Say what's wrong",
    blurb: "The concern you want solved: the fatigue, the pain, the number that won't move.",
    top: '38.3%',
    left: '86.1%',
  },
  {
    num: 3,
    label: 'Get one next step',
    blurb: 'The agent suggests a single change to test or treat it — to try, track, or take to your doctor.',
    top: '80.7%',
    left: '72.3%',
  },
  {
    num: 4,
    label: 'See what happened',
    blurb: 'Do it (with your doctor where it matters), then tell the agent the result, honestly.',
    top: '80.7%',
    left: '27.7%',
  },
  {
    num: 5,
    label: 'Loop toward better',
    blurb: 'Each round rules things in or out and sharpens the picture, until you find what helps.',
    top: '38.3%',
    left: '13.9%',
  },
];

// Arc segments connecting consecutive nodes, each ending in an arrowhead.
// The final segment closes step 5 back to step 1, making the loop explicit.
const LOOP_ARCS = [
  'M59.19,13.13 A38,38 0 0 1 82.23,29.86',
  'M87.91,47.35 A38,38 0 0 1 79.11,74.43',
  'M64.23,85.23 A38,38 0 0 1 35.77,85.23',
  'M20.89,74.43 A38,38 0 0 1 12.09,47.35',
  'M17.77,29.86 A38,38 0 0 1 40.81,13.13',
];

function LoopWheel(): JSX.Element {
  return (
    <div className="loopWheel" role="img" aria-label="The OpenCareLoop care loop: pour in your data, say what's wrong, get one next step, see what happened, then loop toward better health.">
      <svg className="loopRing" viewBox="0 0 100 100" aria-hidden="true">
        <defs>
          <marker
            id="loopArrow"
            viewBox="0 0 10 10"
            refX="6"
            refY="5"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="currentColor" />
          </marker>
        </defs>
        <circle cx="50" cy="50" r="38" className="loopRingTrack" />
        {LOOP_ARCS.map((d, i) => (
          <path key={i} d={d} className="loopRingArc" markerEnd="url(#loopArrow)" />
        ))}
      </svg>
      <div className="loopHub">
        <span className="loopHubMark">↻</span>
        <span className="loopHubText">repeat to improve</span>
      </div>
      {LOOP_STEPS.map((step) => (
        <div key={step.num} className="loopStep" style={{ top: step.top, left: step.left }}>
          <span className="loopStepNum">{step.num}</span>
          <h3 className="loopStepLabel">{step.label}</h3>
          <p className="loopStepBlurb">{step.blurb}</p>
        </div>
      ))}
    </div>
  );
}

function LoopList(): JSX.Element {
  return (
    <ol className="loopList">
      {LOOP_STEPS.map((step) => (
        <li key={step.num} className="loopListItem">
          <span className="loopStepNum">{step.num}</span>
          <div>
            <h3 className="loopStepLabel">{step.label}</h3>
            <p className="loopStepBlurb">{step.blurb}</p>
          </div>
        </li>
      ))}
      <li className="loopListRepeat">↻ then back to the start — each loop gets you closer.</li>
    </ol>
  );
}

export default function Home(): JSX.Element {
  return (
    <Layout
      title="OpenCareLoop"
      description="An AI agent that helps you and your family get to the bottom of health issues — pour in your data, get one change at a time, and loop your way to better health. Private and local to your device.">
      <header className="hero heroCentered">
        <div className="container">
          <h1 className="hero__title">OpenCareLoop</h1>
          <p className="hero__subtitle">Solve your family's health, one loop at a time.</p>
          <Link className="button button--primary button--lg" to="/docs/getting-started">
            Get started
          </Link>
        </div>
      </header>
      <main className="homeMain">
        <div className="container loopSection">
          <LoopWheel />
          <LoopList />
        </div>
      </main>
    </Layout>
  );
}

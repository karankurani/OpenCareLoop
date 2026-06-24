import { Fragment, useEffect } from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';

const RELEASE_DOWNLOAD_URL =
  'https://github.com/karankurani/OpenCareLoop/releases/latest/download/OpenCareLoop.zip';

const LOOP_STEPS = [
  {
    num: 1,
    label: 'Pour in your data',
    blurb: 'Records, symptoms, medicines, lifestyle. The more it knows, the sharper it gets.',
    highlighted: false,
  },
  {
    num: 2,
    label: "Say what's wrong",
    blurb: "The concern you want solved: the fatigue, the pain, the number that won't move.",
    highlighted: false,
  },
  {
    num: 3,
    label: 'Get one next step',
    blurb: 'A single change to test or treat — something to try, track, or take to your doctor.',
    highlighted: false,
  },
  {
    num: 4,
    label: 'See what happened',
    blurb: 'Do it (with your doctor where it matters), then tell the agent the result, honestly.',
    highlighted: false,
  },
  {
    num: 5,
    label: 'Loop toward better',
    blurb: 'Each round rules things in or out and sharpens the picture, until you find what helps.',
    highlighted: true,
  },
];

const SETUP_STEPS = [
  {
    num: '01',
    label: 'Download & unzip',
    blurb: 'Grab the folder. It holds everything the agent needs.',
    highlighted: false,
  },
  {
    num: '02',
    label: 'Open it in your agent',
    blurb: 'Point Claude Code, Codex, or any agent harness at the folder.',
    highlighted: false,
  },
  {
    num: '03',
    label: 'Start talking',
    blurb: "Describe what's going on. The loop begins from there.",
    highlighted: true,
  },
];

export default function Home(): JSX.Element {
  useEffect(() => {
    document.documentElement.classList.add('home-page');
    return () => {
      document.documentElement.classList.remove('home-page');
    };
  }, []);

  return (
    <Layout
      title="OpenCareLoop"
      description="An AI agent that helps you and your family get to the bottom of health issues — pour in your data, get one change at a time, and loop your way to better health. Private and local to your device.">
      <div className="homePage">

        {/* Hero */}
        <div className="homeHero">
          <div className="homeInner homeCentered">
            <div className="homeEyebrow">Private · Local · Open source</div>
            <h1 className="homeTitle">Solve your family's health, one loop at a time.</h1>
            <div className="homeActions">
              <Link className="homeCta" to="/docs/setup">Get started</Link>
            </div>
          </div>
        </div>

        {/* Loop stepper */}
        <div className="homeSection">
          <div className="homeInner">
            <div className="oclSectionHead">
              <h2 className="oclSectionTitle">How the loop works</h2>
              <div className="oclRepeatBadge"><span>↻</span> Repeat to improve</div>
            </div>
            <div className="oclLoop">
              {LOOP_STEPS.map((step, i) => (
                <Fragment key={step.num}>
                  <div className={['oclCard', step.highlighted ? 'oclCardHighlighted' : ''].filter(Boolean).join(' ')}>
                    <div className={['oclNum', step.highlighted ? 'oclNumOutline' : ''].filter(Boolean).join(' ')}>{step.num}</div>
                    <h3 className="oclCardTitle">{step.label}</h3>
                    <p className="oclCardBlurb">{step.blurb}</p>
                  </div>
                  {i < LOOP_STEPS.length - 1 && (
                    <div className={['oclArrow', i === LOOP_STEPS.length - 2 ? 'oclArrowLoop' : ''].filter(Boolean).join(' ')}>
                      {i === LOOP_STEPS.length - 2 ? '↺' : '→'}
                    </div>
                  )}
                </Fragment>
              ))}
            </div>
          </div>
        </div>

        {/* Setup section */}
        <div className="homeSection homeSectionLast">
          <div className="homeInner">
            <div className="oclSetupBox">
              <div className="homeEyebrow">Get started</div>
              <h2 className="oclSetupTitle">Download, unzip and talk.</h2>
              <p className="oclSetupSubtitle">Point your AI agent at the folder. Your data is stored locally on your machine.</p>
              <a
                className="homeCta"
                href={RELEASE_DOWNLOAD_URL}>
                ↓ Download OpenCareLoop.zip
              </a>
              <div className="oclLoop oclSetupSteps">
                {SETUP_STEPS.map((step) => (
                  <div key={step.num} className={['oclCard', step.highlighted ? 'oclCardHighlighted' : ''].filter(Boolean).join(' ')}>
                    <div className="oclSetupNum">{step.num}</div>
                    <h3 className="oclCardTitle">{step.label}</h3>
                    <p className="oclCardBlurb">{step.blurb}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="homeCopyright">Copyright 2026 Karan Kurani.</div>

      </div>
    </Layout>
  );
}

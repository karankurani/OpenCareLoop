import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';

export default function Home(): JSX.Element {
  return (
    <Layout
      title="OpenCareLoop"
      description="User guide for keeping long-term health context organized with OpenCareLoop">
      <header className="hero">
        <div className="container">
          <h1 className="hero__title">OpenCareLoop</h1>
          <p className="hero__subtitle">
            A user guide for building and maintaining a long-term health dossier with an AI agent.
          </p>
          <Link className="button button--primary button--lg" to="/docs/getting-started">
            Start the guide
          </Link>
        </div>
      </header>
      <main className="homeMain">
        <div className="container homeGrid">
          <section className="homePanel">
            <h2>Start clearly</h2>
            <p>
              Capture the person, current concerns, medicines, and the first timeline without
              turning the README into a long manual.
            </p>
          </section>
          <section className="homePanel">
            <h2>Add records safely</h2>
            <p>
              Know what to gather, where to place it, and how to keep original records separate
              from notes and summaries.
            </p>
          </section>
          <section className="homePanel">
            <h2>Keep context current</h2>
            <p>
              Return after new visits, tests, symptoms, or medication changes and update the
              dossier in small, reviewable steps.
            </p>
          </section>
        </div>
      </main>
    </Layout>
  );
}

import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  mainSidebar: [
    {
      type: 'category',
      label: 'Start here',
      collapsed: false,
      items: ['intro', 'non-urgent-use', 'setup', 'first-dossier'],
    },
    {
      type: 'category',
      label: 'Using the loop',
      collapsed: false,
      items: ['continuing-care-loop', 'adding-records', 'talking-to-the-agent'],
    },
  ],
};

export default sidebars;

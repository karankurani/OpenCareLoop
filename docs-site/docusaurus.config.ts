import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";
import { themes as prismThemes } from "prism-react-renderer";

const config: Config = {
    title: "OpenCareLoop",
    tagline: "The AI agent that helps you with your health your entire lifetime.",
    url: "https://karankurani.github.io",
    baseUrl: "/OpenCareLoop/",
    organizationName: "karankurani",
    projectName: "OpenCareLoop",
    trailingSlash: false,

    onBrokenLinks: "throw",
    markdown: {
        hooks: {
            onBrokenMarkdownLinks: "warn",
        },
    },

    i18n: {
        defaultLocale: "en",
        locales: ["en"],
    },

    presets: [
        [
            "classic",
            {
                docs: {
                    sidebarPath: "./sidebars.ts",
                    routeBasePath: "docs",
                },
                blog: false,
                theme: {
                    customCss: "./src/css/custom.css",
                },
            } satisfies Preset.Options,
        ],
    ],

    themeConfig: {
        navbar: {
            title: "OpenCareLoop",
            items: [
                {
                    type: "docSidebar",
                    sidebarId: "mainSidebar",
                    position: "left",
                    label: "Guide",
                },
                {
                    href: "https://github.com/karankurani/OpenCareLoop",
                    label: "GitHub",
                    position: "right",
                },
            ],
        },
        footer: {
            style: "light",
            links: [
                {
                    title: "Guide",
                    items: [
                        {
                            label: "Getting started",
                            to: "/docs/getting-started",
                        },
                        {
                            label: "Adding records",
                            to: "/docs/adding-records",
                        },
                    ],
                },
                {
                    title: "Project",
                    items: [
                        {
                            label: "GitHub",
                            href: "https://github.com/karankurani/OpenCareLoop",
                        },
                    ],
                },
            ],
            copyright: `Copyright ${new Date().getFullYear()} OpenCareLoop contributors.`,
        },
        prism: {
            theme: prismThemes.github,
            darkTheme: prismThemes.dracula,
        },
    } satisfies Preset.ThemeConfig,
};

export default config;

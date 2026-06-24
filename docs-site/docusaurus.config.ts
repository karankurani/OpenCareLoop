import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";
import { themes as prismThemes } from "prism-react-renderer";

const config: Config = {
    title: "OpenCareLoop",
    tagline: "Solve your family's health, one loop at a time.",
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
        colorMode: {
            defaultMode: "light",
            disableSwitch: true,
            respectPrefersColorScheme: false,
        },
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
        prism: {
            theme: prismThemes.github,
        },
    } satisfies Preset.ThemeConfig,
};

export default config;

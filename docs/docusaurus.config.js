// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking
// (when paired with `@ts-check`).
// There are various equivalent ways to declare your Docusaurus config.
// See: https://docusaurus.io/docs/api/docusaurus-config

import { themes as prismThemes } from "prism-react-renderer";

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "ExCore",
  tagline: "Configuration/Registry System designed for deeplearning",
  favicon: "img/logo.ico",

  // Set the production url of your site here
  url: "https://your-docusaurus-site.example.com",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "Asthestarsfalll", // Usually your GitHub org/user name.
  projectName: "ExCore", // Usually your repo name.

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: "en",
    locales: ["zh-Hans", "en"],
  },

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: "./sidebars.js",
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            "https://github.com/facebook/docusaurus/tree/main/packages/create-docusaurus/templates/shared/",
        },
        blog: {
          showReadingTime: true,
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            "https://github.com/facebook/docusaurus/tree/main/packages/create-docusaurus/templates/shared/",
        },
        theme: {
          customCss: "./src/css/custom.css",
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      // image: "./img/docusaurus-social-card.jpg",
      navbar: {
        title: "ExCore",
        logo: {
          alt: "My Site Logo",
          src: "img/logo_light.png",
          srcDark: "img/logo_dark.png",
        },
        style: "dark",
        hideOnScroll: true,
        items: [
          {
            type: "docSidebar",
            sidebarId: "tutorialSidebar",
            position: "left",
            label: "Docs",
          },
          { to: "/blog", label: "Blog", position: "left" },
          {
            href: "https://github.com/Asthestarsfalll/ExCore",
            label: "GitHub",
            position: "right",
          },
          {
            type: "search",
            position: "right",
          },
        ],
      },
      // footer: {
      //   style: "dark",
      //   copyright: `MIT license, ${new Date().getFullYear()}, ExCore all right reserved`,
      // },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ["toml", "yaml", "python"],
        magicComments: [
          // Remember to extend the default highlight class name as well!
          {
            className: "code-block-highlighted-line",
            line: "Highlight",
            block: { start: "Highlight-start", end: "Highlight-end" },
          },
          {
            className: "code-block-error-line",
            line: "Error",
            block: { start: "Error-start", end: "Error-end" },
          },
          {
            className: "code-block-important-line",
            line: "Important",
            block: { start: "Im-start", end: "Im-end" },
          },
        ],
      },
    }),
};

export default config;

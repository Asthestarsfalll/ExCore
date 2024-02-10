import React, { useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import Layout from "@theme/Layout";
import BrowserOnly from "@docusaurus/BrowserOnly";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import styles from "./index.module.css";
import { inject } from "@vercel/analytics";
inject();

import Typical from "react-typical";
import * as config from "./_index.config";
import { useMediaQuery } from "react-responsive";
import { useColorMode } from "@docusaurus/theme-common";

function BlurBackgroundImage() {
  const { isDarkTheme } = useColorMode();
  const anotherImgurl = isDarkTheme
    ? "/img/indexbackground_light.jpg"
    : "/img/indexbackground_dark.jpg";
  const imgurl = !isDarkTheme
    ? "/img/indexbackground_light.jpg"
    : "/img/indexbackground_dark.jpg";
  return (
    <div
      style={{
        backgroundImage: `url(${imgurl})`,
        backgroundAttachment: "fixed",
        backgroundSize: "cover",
        filter: `blur(10px) brightness(${isDarkTheme ? 0.7 : 1})`,
        transform: "scale(1.2)",
        position: "absolute",
        zIndex: 0,
        height: "100%",
        width: "100%",
      }}
    >
      {/* Keep another image loaded */}
      <img src={anotherImgurl} alt="" style={{ display: "none" }} />
    </div>
  );
}

function HomepageBackground() {
  const { siteConfig } = useDocusaurusContext();
  const { isDarkTheme } = useColorMode();
  return (
    <header
      className={clsx("hero themedHead", styles.heroBanner)}
      style={{
        minHeight: "calc(100vh - var(--ifm-navbar-height))",
        backgroundAttachment: "fixed",
        backgroundColor: isDarkTheme ? "#1f1d2e" : "#ebbcba",
      }}
    >
      <BrowserOnly>{BlurBackgroundImage}</BrowserOnly>
      <div className="container" style={{ zIndex: 1 }}>
        <div className="col">
          <div
            className={clsx("col", "col--", styles.centerChild)}
            style={{
              marginTop: "-5em",
            }}
          >
            <BrowserOnly>{RandomImage}</BrowserOnly>
          </div>
          <div
            className={clsx("col", "col--", styles.centerChild)}
            style={{
              alignSelf: "center",
              marginBottom: "30px",
              minHeight: "6em",
            }}
          >
            <p
              className="hero__subtitle"
              style={{
                color: "#7c1823",
              }}
            >
              <Typical
                steps={useMemo(
                  () =>
                    config.subtitles_and_delays.flatMap((x) => [
                      x.text,
                      x.delay,
                    ]),
                  [],
                )}
                loop={Infinity}
                wrapper="span"
              />
            </p>
            {/* <div> */}
            {/*   <a */}
            {/*     className="button button--outline" */}
            {/*     style={{ */}
            {/*       color: "#7a0c28", */}
            {/*       border: "solid 2px", */}
            {/*       textShadow: `0px 0px 3px ${isDarkTheme ? "#000000" : "#FFFFFF"}`, */}
            {/*     }} */}
            {/*     href="/docs" */}
            {/*   > */}
            {/*     Documents */}
            {/*   </a> */}
            {/* </div> */}
          </div>
        </div>
      </div>
    </header>
  );
}

function RandomImage() {
  const [loaded, setLoaded] = useState(false);
  const isMobile = useMediaQuery({ maxWidth: 1024 });
  return (
    <img
      src={"/img/lo.png"}
      className={clsx(styles.randomImage, loaded && styles.loaded)}
      style={{
        width: isMobile ? "40%" : "50%",
        alignSelf: "center",
      }}
      onLoad={() => {
        setLoaded(true);
      }}
    />
  );
}

export default function Home(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout title={`${siteConfig.title}`} description="ExCore">
      <HomepageBackground />
    </Layout>
  );
}

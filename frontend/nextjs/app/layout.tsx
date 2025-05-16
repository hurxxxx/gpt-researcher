import type { Metadata } from "next";
import { Lexend } from "next/font/google";
import PlausibleProvider from "next-plausible";
import { GoogleAnalytics } from '@next/third-parties/google'
import "./globals.css";

const inter = Lexend({ subsets: ["latin"] });

let title = "GPT Researcher";
let description =
  "LLM based autonomous agent that conducts local and web research on any topic and generates a comprehensive report with citations.";
let url = "https://github.com/assafelovic/gpt-researcher";
let ogimage = "/favicon.ico";
let sitename = "GPT Researcher";

export const metadata: Metadata = {
  metadataBase: new URL(url),
  title,
  description,
  icons: {
    icon: "/favicon.ico",
  },
  openGraph: {
    images: [ogimage],
    title,
    description,
    url: url,
    siteName: sitename,
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    images: [ogimage],
    title,
    description,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  return (
    <html className="gptr-root" lang="en">
      <head>
        {/* Matomo Tag Manager */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              var _mtm = window._mtm = window._mtm || [];
              _mtm.push({'mtm.startTime': (new Date().getTime()), 'event': 'mtm.Start'});
              (function() {
                var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
                g.async=true; g.src='https://matomo.giz.ai/js/container_Xmzuy8xC.js'; s.parentNode.insertBefore(g,s);
              })();
            `
          }}
        />
        {/* End Matomo Tag Manager */}
        <PlausibleProvider domain="localhost:3000" />
        <GoogleAnalytics gaId={process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID!} />
      </head>
      <body
        className={`app-container ${inter.className} flex min-h-screen flex-col justify-between`}
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}

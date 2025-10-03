import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/toaster";
import { LayoutWithSidebar } from "@/components/LayoutWithSidebar";

export const metadata: Metadata = {
  title: "Zemixity",
  description: "AI-powered search with Gemini 2.0",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <LayoutWithSidebar>
            {children}
          </LayoutWithSidebar>
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}

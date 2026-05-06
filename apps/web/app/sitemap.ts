import type { MetadataRoute } from "next";

const baseUrl = "https://goashlandesports.com";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = [
    "",
    "/roster",
    "/staff",
    "/schedule",
    "/news",
    "/stream",
    "/recruit",
    "/facility",
    "/hof",
    "/support",
  ];

  return routes.map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
  }));
}

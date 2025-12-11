-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Item" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "title" TEXT NOT NULL,
    "url" TEXT NOT NULL,
    "source" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "summaryEn" TEXT NOT NULL DEFAULT '',
    "summaryZh" TEXT NOT NULL DEFAULT '',
    "whyItMattersEn" TEXT NOT NULL DEFAULT '',
    "whyItMattersZh" TEXT NOT NULL DEFAULT '',
    "keywordsEn" TEXT NOT NULL DEFAULT '',
    "keywordsZh" TEXT NOT NULL DEFAULT '',
    "category" TEXT NOT NULL,
    "score" REAL NOT NULL,
    "publishedAt" DATETIME NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO "new_Item" ("category", "createdAt", "id", "publishedAt", "score", "source", "summary", "title", "type", "url") SELECT "category", "createdAt", "id", "publishedAt", "score", "source", "summary", "title", "type", "url" FROM "Item";
DROP TABLE "Item";
ALTER TABLE "new_Item" RENAME TO "Item";
CREATE UNIQUE INDEX "Item_url_key" ON "Item"("url");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;

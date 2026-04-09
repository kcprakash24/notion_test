# Notion → GitHub Blog Sync

A GitHub Actions workflow that pulls blog posts from a Notion database into your repository as `.mdx` files — triggered manually whenever you want.

---

## What It Does

- Fetches all pages from your Notion database where `Status = Live`
- Converts each page to a `.mdx` file with frontmatter
- Downloads all images locally into an `assets/` folder
- Commits and pushes everything to your repo

---

## Repo Structure

```
your-repo/
├── .github/
│   └── workflows/
│       └── sync.yml
├── blogs/
│   └── your-blog-slug/
│       ├── index.mdx
│       └── assets/
│           ├── image1.png
│           └── image2.png
├── sync_notion.py
└── requirements.txt
```

---

## Notion Database Schema

Your Notion database must have these properties:

| Property Name | Type | Purpose |
|---|---|---|
| `Title` | Title | Blog title |
| `Status` | Status | Set to `Live` to include in sync |
| `Slug` | Text | Folder name in repo e.g. `my-first-blog` |
| `Published Date` | Date | Appears in frontmatter |
| `Tags` | Multi-select | Appears in frontmatter |
| `Summary` | Text | One line description |

---

## Generated Frontmatter

Each `index.mdx` will have this at the top, populated from Notion:

```
---
title: 'Your Blog Title'
date: '2026-04-08'
tags: ['tag1', 'tag2']
draft: false
summary: 'Your summary here.'
authors: ['default']
layout: PostSimple
---
```

---

## One-Time Setup

### 1. Create a Notion Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **New integration**
3. Name it (e.g. `github-sync`), select your workspace, click **Save**
4. Copy the **Internal Integration Token** — starts with `secret_...`

### 2. Connect Integration to Your Database

1. Open your Notion database
2. Click `...` menu (top right) → **Connections**
3. Find and add your integration

### 3. Get Your Database ID

From your database URL:
```
https://www.notion.so/yourworkspace/<DATABASE_ID>?v=...
```
Copy the 32-char string between the last `/` and `?`

### 4. Add GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|---|---|
| `NOTION_TOKEN` | Your `secret_...` integration token |
| `NOTION_DATABASE_ID` | Your 32-char database ID |

---

## How to Trigger

1. Go to your repo → **Actions** tab
2. Click **Sync Notion Blogs** in the left sidebar
3. Click **Run workflow** → **Run workflow**

The workflow will run, sync all `Live` pages, and commit the results to your repo.

---

## How Sync Works

- Every trigger does a **full overwrite** of the `blogs/` folder
- Any page set to `Live` in Notion will appear in the repo
- Any page removed from `Live` will be removed from the repo
- Edits made in Notion will reflect on the next trigger
- Images are downloaded locally so the repo is fully self-contained — no dependency on Notion's URLs

---

## Dependencies

- `notion-client==2.2.1`
- `requests==2.31.0`

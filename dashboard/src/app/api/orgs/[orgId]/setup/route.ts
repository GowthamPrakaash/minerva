/**
 * POST /api/orgs/[orgId]/setup
 *
 * Triggers async creation of the PostgreSQL schema for this org.
 *
 * This endpoint is called immediately after POST /api/orgs creates a new org.
 * It starts schema creation in the background and returns immediately with
 * { status: "provisioning" }. The frontend should poll GET /api/orgs/[orgId]/status
 * until it receives { status: "ready" }.
 *
 * WHY NOT AWAIT DIRECTLY?
 * createOrgSchema runs DDL which can take 1-2s. We don't want the org creation
 * request to hang waiting for it. Returning immediately gives a better UX.
 *
 * HOW BACKGROUND WORKS IN NEXT.JS:
 * We use `waitUntil` from the Vercel edge runtime to keep the process alive
 * after the response is returned, OR we simply kick off the promise without
 * awaiting it (fire-and-forget, works on Node.js runtimes).
 */

import { auth } from "@/auth";
import { db } from "@/db";
import { organizations, orgMembers } from "@/db/schema";
import { createOrgSchema } from "@/db/setup-tenant";
import { eq, and } from "drizzle-orm";
import { NextResponse } from "next/server";

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ orgId: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { orgId } = await params;

  // Verify the user belongs to this org
  const [membership] = await db
    .select()
    .from(orgMembers)
    .where(
      and(eq(orgMembers.userId, session.user.id), eq(orgMembers.orgId, orgId))
    );

  if (!membership) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  // Verify org exists and is active
  const [org] = await db
    .select()
    .from(organizations)
    .where(eq(organizations.id, orgId));

  if (!org) {
    return NextResponse.json({ error: "Org not found" }, { status: 404 });
  }

  // Fire and forget — schema creation runs in background
  // The response returns immediately; frontend polls /api/orgs/[orgId]/status
  createOrgSchema(orgId).catch((err) => {
    console.error(`[setup] Failed to create schema for org ${orgId}:`, err);
  });

  return NextResponse.json({ status: "provisioning", orgId }, { status: 202 });
}

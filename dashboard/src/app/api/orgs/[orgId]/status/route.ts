/**
 * GET /api/orgs/[orgId]/status
 *
 * Polls whether the org's PostgreSQL schema has been created yet.
 * Returns { status: "ready" } once the schema exists, or { status: "provisioning" } if not.
 *
 * The frontend should poll this after calling POST /api/orgs/[orgId]/setup,
 * showing a loading/provisioning screen until "ready".
 */

import { auth } from "@/auth";
import { pool } from "@/db";
import { db } from "@/db";
import { orgMembers } from "@/db/schema";
import { eq, and } from "drizzle-orm";
import { NextResponse } from "next/server";

export async function GET(
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

  // Check if the schema exists in pg_catalog
  const client = await pool.connect();
  try {
    const result = await client.query<{ exists: boolean }>(
      `SELECT EXISTS (
        SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname = $1
      ) AS exists`,
      [`org_${orgId}`]
    );

    const schemaExists = result.rows[0]?.exists ?? false;

    return NextResponse.json({
      orgId,
      status: schemaExists ? "ready" : "provisioning",
    });
  } finally {
    client.release();
  }
}

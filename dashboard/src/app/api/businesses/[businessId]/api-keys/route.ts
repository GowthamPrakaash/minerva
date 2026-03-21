import { auth } from "@/auth";
import { db } from "@/db";
import { businesses } from "@/db/schema";
import { getTenantSchema } from "@/db/tenant-schema";
import { eq, and } from "drizzle-orm";
import { NextResponse } from "next/server";
import { createHash, randomBytes } from "crypto";

function hashKey(key: string): string {
  return createHash("sha256").update(key).digest("hex");
}

function generateApiKey(): string {
  const key = randomBytes(32).toString("hex");
  return `mnrv_${key}`;
}

export async function GET(
  req: Request,
  { params }: { params: Promise<{ businessId: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { businessId } = await params;

  const [business] = await db
    .select()
    .from(businesses)
    .where(
      and(eq(businesses.id, businessId), eq(businesses.isActive, true))
    );

  if (!business) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const { apiKeys } = getTenantSchema(business.orgId);
  const keys = await db
    .select({
      id: apiKeys.id,
      name: apiKeys.name,
      keyPrefix: apiKeys.keyPrefix,
      createdOn: apiKeys.createdOn,
      lastUsed: apiKeys.lastUsed,
    })
    .from(apiKeys);

  return NextResponse.json(keys);
}

export async function POST(
  req: Request,
  { params }: { params: Promise<{ businessId: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { businessId } = await params;
  const { name } = await req.json();

  if (!name) {
    return NextResponse.json({ error: "Name is required" }, { status: 400 });
  }

  const [business] = await db
    .select()
    .from(businesses)
    .where(eq(businesses.id, businessId));

  if (!business) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const rawKey = generateApiKey();
  const keyPrefix = rawKey.substring(0, 13) + "...";
  const apiSecretHash = hashKey(rawKey);

  const { apiKeys } = getTenantSchema(business.orgId);
  const [key] = await db
    .insert(apiKeys)
    .values({
      apiKey: rawKey,
      name,
      keyPrefix,
      apiSecretHash,
    })
    .returning();

  return NextResponse.json(
    { ...key, key: rawKey },
    { status: 201 }
  );
}

export async function DELETE(
  req: Request,
  { params }: { params: Promise<{ businessId: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { businessId } = await params;
  const { searchParams } = new URL(req.url);
  const keyId = searchParams.get("keyId");

  if (!keyId) {
    return NextResponse.json(
      { error: "Key ID is required" },
      { status: 400 }
    );
  }

  const [business] = await db
    .select()
    .from(businesses)
    .where(eq(businesses.id, businessId));

  if (!business) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const { apiKeys } = getTenantSchema(business.orgId);
  await db
    .delete(apiKeys)
    .where(eq(apiKeys.id, keyId));

  return NextResponse.json({ success: true });
}

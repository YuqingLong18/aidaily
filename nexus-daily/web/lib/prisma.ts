import { PrismaClient } from '@prisma/client'
import path from 'path'

const globalForPrisma = global as unknown as { prisma: PrismaClient }

// Resolve DATABASE_URL to absolute path if it's relative
function resolveDatabaseUrl(): string | undefined {
  const dbUrl = process.env.DATABASE_URL
  if (!dbUrl) return undefined
  
  // If it's a file: URL with a relative path, convert to absolute
  if (dbUrl.startsWith('file:')) {
    const filePath = dbUrl.replace(/^file:/, '')
    
    // If it's already absolute (starts with /), return as-is
    if (path.isAbsolute(filePath)) {
      return dbUrl
    }
    
    // If it's relative, resolve it relative to the project root
    // In Next.js, process.cwd() is the project root (web/ directory)
    const projectRoot = process.cwd()
    const absolutePath = path.resolve(projectRoot, filePath)
    
    console.log(`[prisma.ts] Resolved relative DATABASE_URL: ${dbUrl} -> file:${absolutePath}`)
    return `file:${absolutePath}`
  }
  
  return dbUrl
}

// Override DATABASE_URL if it's relative
const resolvedDbUrl = resolveDatabaseUrl()
if (resolvedDbUrl && resolvedDbUrl !== process.env.DATABASE_URL) {
  process.env.DATABASE_URL = resolvedDbUrl
  console.log(`[prisma.ts] Using resolved DATABASE_URL: ${resolvedDbUrl.substring(0, 80)}...`)
}

export const prisma = globalForPrisma.prisma || new PrismaClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma

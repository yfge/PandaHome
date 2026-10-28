import { Protected } from "@/components/auth/protected";
import { P2pPageClient } from "./page-client";

export default function P2pPage() {
  return <Protected><P2pPageClient /></Protected>;
}

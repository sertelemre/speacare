import { AuthGuard } from "@/components/auth/AuthGuard";
import { LeftSidebar } from "@/components/layout/LeftSidebar";
import { MainContent } from "@/components/layout/MainContent";
import { RightSidebar } from "@/components/layout/RightSidebar";
import { TopBar } from "@/components/layout/TopBar";

export default function HomePage() {
  return (
    <AuthGuard>
      <div className="flex h-screen w-full bg-white dark:bg-gray-950">
        <LeftSidebar />
        <div className="flex flex-1 flex-col">
          <TopBar />
          <div className="flex flex-1 overflow-hidden">
            <MainContent />
            <RightSidebar />
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}

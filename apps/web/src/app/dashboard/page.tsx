import { AuthGuard } from "@/components/auth/AuthGuard";
import { LeftSidebar } from "@/components/layout/LeftSidebar";
import { MainContent } from "@/components/layout/MainContent";
import { RightSidebar } from "@/components/layout/RightSidebar";

export default function DashboardPage() {
  return (
    <AuthGuard>
      <div className="flex h-screen w-full bg-white dark:bg-gray-950 overflow-hidden">
        <LeftSidebar />
        <div className="flex flex-1 flex-col min-h-0">
          <div className="flex flex-1 min-h-0">
            <MainContent />
            <RightSidebar />
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}

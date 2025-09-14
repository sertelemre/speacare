"use client";

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDocumentStore } from '@/store/documentStore';
import api from '@/lib/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileText, FileCheck2 } from "lucide-react";

// TODO: This should come from a dynamic context, not be hardcoded.
const CHANNEL_ID = 1;

interface Document {
    id: number;
    title: string;
    doc_type: 'summary' | 'consensus' | string; // Allow other types but specify common ones
    content_md: string;
    created_at: string;
}

const fetchDocuments = async (channelId: number) => {
    // This endpoint doesn't exist yet, we'll need to add it.
    // For now, we'll assume it exists and will return an empty array.
    try {
        const { data } = await api.get(`/api/channels/${channelId}/documents/`);
        return data;
    } catch (e) {
        console.warn("Failed to fetch documents, endpoint might not exist yet.");
        return [];
    }
};

function DocumentList() {
    const { documents, setDocuments } = useDocumentStore();

    const { data: initialDocs, isLoading } = useQuery({
        queryKey: ['documents', CHANNEL_ID],
        queryFn: () => fetchDocuments(CHANNEL_ID),
        enabled: !!CHANNEL_ID,
    });

    React.useEffect(() => {
        if (initialDocs) {
            setDocuments(initialDocs);
        }
    }, [initialDocs, setDocuments]);

    const getDocIcon = (docType: Document['doc_type']) => {
        switch (docType) {
            case 'summary':
                return <FileText className="h-5 w-5 mr-3 text-blue-500" />;
            case 'consensus':
                return <FileCheck2 className="h-5 w-5 mr-3 text-green-500" />;
            default:
                return <FileText className="h-5 w-5 mr-3 text-gray-500" />;
        }
    }

    return (
        <div className="mt-4 space-y-3">
            {isLoading && <p className="text-sm text-gray-500">Loading...</p>}
            {documents.map(doc => (
                <div key={doc.id} className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700">
                    <div className="flex items-center">
                        {getDocIcon(doc.doc_type)}
                        <div>
                            <h3 className="font-semibold text-sm leading-tight">{doc.doc_type === 'summary' ? 'Round Summary' : 'Consensus Document'}</h3>
                            <p className="text-xs text-gray-500">{new Date(doc.created_at).toLocaleString()}</p>
                        </div>
                    </div>
                </div>
            ))}
            {!isLoading && documents.length === 0 && <p className="text-sm text-gray-500">No documents yet.</p>}
        </div>
    );
}


export function RightSidebar() {
  return (
    <aside className="w-80 flex-shrink-0 border-l border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900">
      <Tabs defaultValue="notes" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="notes">Notes</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
        </TabsList>
        <TabsContent value="notes">
            <div className="mt-4">
                <div className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
                <h3 className="font-semibold">Meeting Summary</h3>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-sm">
                    <li>Decision: Proceed with A/B test.</li>
                    <li>Action: PM to define test segments.</li>
                    <li>Risk: Potential churn from enterprise clients.</li>
                </ul>
                </div>
            </div>
        </TabsContent>
        <TabsContent value="documents">
            <DocumentList />
        </TabsContent>
      </Tabs>
    </aside>
  );
}

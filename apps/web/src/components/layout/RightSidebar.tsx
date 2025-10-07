"use client";

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useDocumentStore } from '@/store/documentStore';
import { useChannelStore } from '@/store/channelStore';
import { useBotStore, type Bot } from '@/store/botStore';
import api from '@/lib/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileText, FileCheck2, Settings, Plus, X, Edit, Save, Bot as BotIcon } from "lucide-react";
import { toast } from 'sonner';

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
    } catch {
        console.warn("Failed to fetch documents, endpoint might not exist yet.");
        return [];
    }
};

const fetchChannelBots = async (channelId: number): Promise<any[]> => {
    const { data } = await api.get(`/api/channels/${channelId}/bots/`);
    return data;
};

const fetchProjects = async () => {
    const { data } = await api.get('/api/projects/');
    return data;
};

const fetchBots = async () => {
    const { data } = await api.get('/api/bots/');
    return data;
};

const updateChannel = async (channelId: number, channelData: any) => {
    const { data } = await api.patch(`/api/channels/${channelId}/`, channelData);
    return data;
};

const addBotToChannel = async (channelId: number, botId: number) => {
    const { data } = await api.post(`/api/channels/${channelId}/invite-bot/`, { bot_id: botId });
    return data;
};

const removeBotFromChannel = async (channelId: number, botId: number) => {
    await api.delete(`/api/channels/${channelId}/bots/${botId}/`);
};

const toggleBotActive = async (channelId: number, botId: number, isActive: boolean) => {
    const { data } = await api.patch(`/api/channels/${channelId}/bots/${botId}/`, { is_active: isActive });
    return data;
};

const addProjectToChannel = async (channelId: number, projectId: number) => {
    const { data } = await api.patch(`/api/channels/${channelId}/`, { projects: [projectId] });
    return data;
};

const removeProjectFromChannel = async (channelId: number, projectId: number) => {
    // Get current projects and remove the specified one
    const channel = await api.get(`/api/channels/${channelId}/`);
    const currentProjects = channel.data.projects || [];
    const updatedProjects = currentProjects.filter((p: any) => p.id !== projectId);
    const { data } = await api.patch(`/api/channels/${channelId}/`, { projects: updatedProjects.map((p: any) => p.id) });
    return data;
};

function ChannelInfo() {
    const { selectedChannel } = useChannelStore();
    const [isEditing, setIsEditing] = useState(false);
    const [editName, setEditName] = useState('');
    const [editDescription, setEditDescription] = useState('');
    const [isAddBotOpen, setIsAddBotOpen] = useState(false);
    const [isAddProjectOpen, setIsAddProjectOpen] = useState(false);
    const [selectedBotId, setSelectedBotId] = useState<number | null>(null);
    const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
    
    const queryClient = useQueryClient();

    const { data: channelBots } = useQuery({
        queryKey: ['channel-bots', selectedChannel?.id],
        queryFn: () => fetchChannelBots(selectedChannel!.id),
        enabled: !!selectedChannel?.id,
    });

    // Debug: Log the data structures
    React.useEffect(() => {
        console.log('Selected Channel:', selectedChannel);
        console.log('Channel Bots:', channelBots);
    }, [selectedChannel, channelBots]);

    const { data: allProjects } = useQuery({
        queryKey: ['projects'],
        queryFn: fetchProjects,
    });

    const { data: allBots } = useQuery({
        queryKey: ['bots'],
        queryFn: fetchBots,
    });

    const updateChannelMutation = useMutation({
        mutationFn: (channelData: any) => updateChannel(selectedChannel!.id, channelData),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channels'] });
            setIsEditing(false);
            toast.success('Channel updated successfully!');
        },
        onError: (error) => {
            toast.error('Failed to update channel');
            console.error('Error updating channel:', error);
        },
    });

    const addBotMutation = useMutation({
        mutationFn: (botId: number) => addBotToChannel(selectedChannel!.id, botId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channel-bots', selectedChannel?.id] });
            setIsAddBotOpen(false);
            setSelectedBotId(null);
            toast.success('Bot added to channel!');
        },
        onError: (error) => {
            toast.error('Failed to add bot to channel');
            console.error('Error adding bot:', error);
        },
    });

    const removeBotMutation = useMutation({
        mutationFn: (botId: number) => removeBotFromChannel(selectedChannel!.id, botId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channel-bots', selectedChannel?.id] });
            toast.success('Bot removed from channel!');
        },
        onError: (error) => {
            toast.error('Failed to remove bot from channel');
            console.error('Error removing bot:', error);
        },
    });

    const toggleBotMutation = useMutation({
        mutationFn: ({ botId, isActive }: { botId: number, isActive: boolean }) => 
            toggleBotActive(selectedChannel!.id, botId, isActive),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channel-bots', selectedChannel?.id] });
            toast.success('Bot status updated!');
        },
        onError: (error) => {
            toast.error('Failed to update bot status');
            console.error('Error updating bot:', error);
        },
    });

    const addProjectMutation = useMutation({
        mutationFn: (projectId: number) => addProjectToChannel(selectedChannel!.id, projectId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channels'] });
            setIsAddProjectOpen(false);
            setSelectedProjectId(null);
            toast.success('Project added to channel!');
        },
        onError: (error) => {
            toast.error('Failed to add project to channel');
            console.error('Error adding project:', error);
        },
    });

    const removeProjectMutation = useMutation({
        mutationFn: (projectId: number) => removeProjectFromChannel(selectedChannel!.id, projectId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channels'] });
            toast.success('Project removed from channel!');
        },
        onError: (error) => {
            toast.error('Failed to remove project from channel');
            console.error('Error removing project:', error);
        },
    });

    const handleEditClick = () => {
        setEditName(selectedChannel?.name || '');
        setEditDescription(selectedChannel?.description || '');
        setIsEditing(true);
    };

    const handleSaveClick = () => {
        if (!editName.trim()) {
            toast.error('Channel name is required');
            return;
        }

        updateChannelMutation.mutate({
            name: editName.trim(),
            description: editDescription.trim(),
        });
    };

    const handleAddBot = () => {
        if (!selectedBotId) {
            toast.error('Please select a bot');
            return;
        }
        addBotMutation.mutate(selectedBotId);
    };

    const handleAddProject = () => {
        if (!selectedProjectId) {
            toast.error('Please select a project');
            return;
        }
        addProjectMutation.mutate(selectedProjectId);
    };

    if (!selectedChannel) {
        return (
            <div className="text-center py-8">
                <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">No channel selected</p>
            </div>
        );
    }

    const availableProjects = allProjects?.filter((project: any) => 
        !selectedChannel.projects?.some((p: any) => p.id === project.id)
    ) || [];

    const availableBots = allBots?.filter((bot: any) => 
        !channelBots?.some((cb: any) => cb.bot?.id === bot.id)
    ) || [];

    return (
        <div className="space-y-6">
            {/* Channel Basic Info */}
            <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">Channel Info</h3>
                    {!isEditing && (
                        <Button size="sm" variant="outline" onClick={handleEditClick}>
                            <Edit className="h-4 w-4 mr-1" />
                            Edit
                        </Button>
                    )}
                </div>
                
                {isEditing ? (
                    <div className="space-y-3">
                        <div>
                            <Label htmlFor="channel-name">Name</Label>
                            <Input
                                id="channel-name"
                                value={editName}
                                onChange={(e) => setEditName(e.target.value)}
                                placeholder="Channel name"
                            />
                        </div>
                        <div>
                            <Label htmlFor="channel-description">Description</Label>
                            <Textarea
                                id="channel-description"
                                value={editDescription}
                                onChange={(e) => setEditDescription(e.target.value)}
                                placeholder="Channel description"
                                rows={3}
                            />
                        </div>
                        <div>
                            <Label>Connected Projects</Label>
                            <div className="space-y-2 mt-2">
                                {selectedChannel.projects && selectedChannel.projects.length > 0 ? (
                                    selectedChannel.projects.map((project: any, index: number) => (
                                        <div key={project.id || `project-${index}`} className="flex items-center justify-between bg-gray-50 dark:bg-gray-700 rounded p-2">
                                            <span className="text-sm text-gray-900 dark:text-gray-100">{project.name || project.title || 'Unnamed Project'}</span>
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                onClick={() => removeProjectMutation.mutate(project.id)}
                                                disabled={removeProjectMutation.isPending}
                                            >
                                                <X className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    ))
                                ) : (
                                    <p className="text-sm text-gray-500 dark:text-gray-400">No projects connected</p>
                                )}
                                <Dialog open={isAddProjectOpen} onOpenChange={setIsAddProjectOpen}>
                                    <DialogTrigger asChild>
                                        <Button size="sm" variant="outline" className="w-full">
                                            <Plus className="h-4 w-4 mr-1" />
                                            Add Project
                                        </Button>
                                    </DialogTrigger>
                                    <DialogContent>
                                        <DialogHeader>
                                            <DialogTitle>Add Project to Channel</DialogTitle>
                                            <DialogDescription>
                                                Select a project to connect to this channel.
                                            </DialogDescription>
                                        </DialogHeader>
                                        <div className="space-y-4">
                                            <div>
                                                <Label>Select Project</Label>
                                                <Select value={selectedProjectId?.toString() || ''} onValueChange={(value) => setSelectedProjectId(parseInt(value))}>
                                                    <SelectTrigger>
                                                        <SelectValue placeholder="Choose a project" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {availableProjects.map((project: any, index: number) => (
                                                            <SelectItem key={project.id || `available-project-${index}`} value={project.id.toString()}>
                                                                {project.name || project.title || 'Unnamed Project'}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div className="flex justify-end space-x-2">
                                                <Button variant="outline" onClick={() => setIsAddProjectOpen(false)}>
                                                    Cancel
                                                </Button>
                                                <Button onClick={handleAddProject} disabled={addProjectMutation.isPending}>
                                                    {addProjectMutation.isPending ? 'Adding...' : 'Add Project'}
                                                </Button>
                                            </div>
                                        </div>
                                    </DialogContent>
                                </Dialog>
                            </div>
                        </div>
                        <div className="flex space-x-2">
                            <Button size="sm" onClick={handleSaveClick} disabled={updateChannelMutation.isPending}>
                                <Save className="h-4 w-4 mr-1" />
                                {updateChannelMutation.isPending ? 'Saving...' : 'Save'}
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => setIsEditing(false)}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                ) : (
                    <div>
                        <div className="flex items-center justify-between">
                            <h4 className="font-medium text-gray-900 dark:text-gray-100">{selectedChannel.name}</h4>
                            <div className="flex items-center space-x-2">
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                    selectedChannel.is_active 
                                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100' 
                                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
                                }`}>
                                    {selectedChannel.is_active ? 'Active' : 'Inactive'}
                                </span>
                                {selectedChannel.waiting_for_user && (
                                    <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100">
                                        Waiting for user
                                    </span>
                                )}
                            </div>
                        </div>
                        <div className="mt-2 flex space-x-2">
                            <Button 
                                size="sm" 
                                variant={selectedChannel.is_active ? "destructive" : "default"}
                                onClick={() => updateChannelMutation.mutate({ is_active: !selectedChannel.is_active })}
                                disabled={updateChannelMutation.isPending}
                            >
                                {selectedChannel.is_active ? 'Deactivate Channel' : 'Activate Channel'}
                            </Button>
                        </div>
                        {selectedChannel.description && (
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                {selectedChannel.description}
                            </p>
                        )}
                        
                        {/* Connected Projects */}
                        <div className="mt-4">
                            <div className="flex items-center justify-between mb-2">
                                <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300">Connected Projects</h5>
                                <Dialog open={isAddProjectOpen} onOpenChange={setIsAddProjectOpen}>
                                    <DialogTrigger asChild>
                                        <Button size="sm" variant="outline">
                                            <Plus className="h-3 w-3 mr-1" />
                                            Add
                                        </Button>
                                    </DialogTrigger>
                                    <DialogContent>
                                        <DialogHeader>
                                            <DialogTitle>Add Project to Channel</DialogTitle>
                                            <DialogDescription>
                                                Select a project to connect to this channel.
                                            </DialogDescription>
                                        </DialogHeader>
                                        <div className="space-y-4">
                                            <div>
                                                <Label>Select Project</Label>
                                                <Select value={selectedProjectId?.toString() || ''} onValueChange={(value) => setSelectedProjectId(parseInt(value))}>
                                                    <SelectTrigger>
                                                        <SelectValue placeholder="Choose a project" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {availableProjects.map((project: any, index: number) => (
                                                            <SelectItem key={project.id || `available-project-${index}`} value={project.id.toString()}>
                                                                {project.name || project.title || 'Unnamed Project'}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div className="flex justify-end space-x-2">
                                                <Button variant="outline" onClick={() => setIsAddProjectOpen(false)}>
                                                    Cancel
                                                </Button>
                                                <Button onClick={handleAddProject} disabled={addProjectMutation.isPending}>
                                                    {addProjectMutation.isPending ? 'Adding...' : 'Add Project'}
                                                </Button>
                                            </div>
                                        </div>
                                    </DialogContent>
                                </Dialog>
                            </div>
                            
                            {selectedChannel.projects && selectedChannel.projects.length > 0 ? (
                                <div className="space-y-1">
                                    {selectedChannel.projects.map((project: any, index: number) => (
                                        <div key={project.id || `project-${index}`} className="flex items-center justify-between bg-gray-50 dark:bg-gray-700 rounded p-2">
                                            <span className="text-sm text-gray-900 dark:text-gray-100">{project.name || project.title || 'Unnamed Project'}</span>
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                onClick={() => removeProjectMutation.mutate(project.id)}
                                                disabled={removeProjectMutation.isPending}
                                            >
                                                <X className="h-3 w-3" />
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-sm text-gray-500 dark:text-gray-400">No projects connected</p>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Channel Bots */}
            <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">Channel Bots</h3>
                    <Dialog open={isAddBotOpen} onOpenChange={setIsAddBotOpen}>
                        <DialogTrigger asChild>
                            <Button size="sm" variant="outline">
                                <Plus className="h-4 w-4 mr-1" />
                                Add Bot
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Add Bot to Channel</DialogTitle>
                                <DialogDescription>
                                    Select a bot to add to this channel.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4">
                                <div>
                                    <Label>Select Bot</Label>
                                    <Select value={selectedBotId?.toString() || ''} onValueChange={(value) => setSelectedBotId(parseInt(value))}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Choose a bot" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {availableBots.map((bot: any, index: number) => (
                                                <SelectItem key={bot.id || `available-bot-${index}`} value={bot.id.toString()}>
                                                    {bot.name || bot.title || 'Unnamed Bot'}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="flex justify-end space-x-2">
                                    <Button variant="outline" onClick={() => setIsAddBotOpen(false)}>
                                        Cancel
                                    </Button>
                                    <Button onClick={handleAddBot} disabled={addBotMutation.isPending}>
                                        {addBotMutation.isPending ? 'Adding...' : 'Add Bot'}
                                    </Button>
                                </div>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                
                <div className="space-y-2">
                    {channelBots && channelBots.length > 0 ? (
                        channelBots.map((channelBot: any, index: number) => (
                            <div key={channelBot.id || `bot-${index}`} className="flex items-center justify-between bg-gray-50 dark:bg-gray-700 rounded p-2">
                                <div className="flex items-center space-x-2">
                                    <BotIcon className="h-4 w-4 text-blue-500" />
                                    <span className="text-sm text-gray-900 dark:text-gray-100">
                                        {channelBot.bot?.name || channelBot.bot?.title || 'Unnamed Bot'}
                                    </span>
                                    <span className={`px-2 py-1 text-xs rounded-full ml-2 ${
                                        channelBot.is_active 
                                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100' 
                                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
                                    }`}>
                                        {channelBot.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </div>
                                <div className="flex space-x-1">
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => toggleBotMutation.mutate({ 
                                            botId: channelBot.id, 
                                            isActive: !channelBot.is_active 
                                        })}
                                        disabled={toggleBotMutation.isPending}
                                    >
                                        {channelBot.is_active ? 'Deactivate' : 'Activate'}
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => removeBotMutation.mutate(channelBot.bot?.id || channelBot.id)}
                                        disabled={removeBotMutation.isPending}
                                    >
                                        <X className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                        ))
                    ) : (
                        <p className="text-sm text-gray-500 dark:text-gray-400">No bots in this channel</p>
                    )}
                </div>
            </div>
        </div>
    );
}

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
        <div className="space-y-3">
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

import { useThreadStore } from '@/store/threadStore';
import { useProjectStore } from '@/store/projectStore';
import { ThreadView } from './ThreadView';


export function RightSidebar() {
  const { activeThreadId } = useThreadStore();
  const { selectedProject } = useProjectStore();
  const { isBotViewActive } = useBotStore();

  // Don't show RightSidebar when a project or bot view is active
  if (selectedProject || isBotViewActive) {
    return null;
  }

  return (
    <aside className="w-96 flex-shrink-0 border-l border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900 flex flex-col min-h-0">
      {activeThreadId ? (
        <ThreadView />
      ) : (
        <div className="flex flex-col h-full min-h-0">
          <div className="flex-shrink-0 p-4 pb-0">
            <Tabs defaultValue="channel-info" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="channel-info">Channel Info</TabsTrigger>
                <TabsTrigger value="notes">Notes</TabsTrigger>
                <TabsTrigger value="documents">Documents</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
          <div className="flex-1 p-4 pt-2 overflow-y-auto min-h-0">
            <Tabs defaultValue="channel-info" className="w-full h-full">
              <TabsContent value="channel-info" className="h-full">
                <ChannelInfo />
              </TabsContent>
              <TabsContent value="notes" className="h-full">
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
              <TabsContent value="documents" className="h-full">
                <DocumentList />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      )}
    </aside>
  );
}

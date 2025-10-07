"use client";

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import api from '@/lib/api';
import { Bot, Settings, Plus, Hash, FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { useChannelStore } from '@/store/channelStore';
import { useProjectStore } from '@/store/projectStore';
import { useBotStore } from '@/store/botStore';

interface Channel {
  id: number;
  name: string;
  description: string;
  projects: number[];
  is_active: boolean;
}

interface Project {
  id: number;
  name: string;
  description: string;
  details: string;
  created_by: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  asset_count?: number;
}

const fetchChannels = async (): Promise<Channel[]> => {
  const { data } = await api.get('/api/channels/');
  return data;
};

const fetchProjects = async (): Promise<Project[]> => {
  const { data } = await api.get('/api/projects/');
  return data;
};

const createChannel = async (channelData: { name: string; description: string; projects?: number[] }): Promise<Channel> => {
  const { data } = await api.post('/api/channels/', channelData);
  return data;
};

const createProject = async (projectData: { name: string; description: string; details: string }): Promise<Project> => {
  const { data } = await api.post('/api/projects/', projectData);
  return data;
};

export function LeftSidebar() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isCreateProjectDialogOpen, setIsCreateProjectDialogOpen] = useState(false);
  const [newChannelName, setNewChannelName] = useState('');
  const [newChannelDescription, setNewChannelDescription] = useState('');
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [newProjectDetails, setNewProjectDetails] = useState('');
  const queryClient = useQueryClient();
  const { selectedChannel, setSelectedChannel } = useChannelStore();
  const { selectedProject, setSelectedProject } = useProjectStore();
  const { setSelectedBot, setBotViewActive, isBotViewActive } = useBotStore();

  const { data: channels, isLoading, error } = useQuery<Channel[]>({
    queryKey: ['channels'],
    queryFn: fetchChannels,
  });

  const { data: projects } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  });

  // Auto-select first channel when channels are loaded and no channel is selected
  useEffect(() => {
    if (channels && channels.length > 0 && !selectedChannel && !selectedProject && !isBotViewActive) {
      setSelectedChannel(channels[0]);
    }
  }, [channels, selectedChannel, selectedProject, isBotViewActive, setSelectedChannel]);

  const createChannelMutation = useMutation({
    mutationFn: createChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      setIsCreateDialogOpen(false);
      setNewChannelName('');
      setNewChannelDescription('');
      setSelectedProjects([]);
      toast.success('Channel created successfully!');
    },
    onError: (error) => {
      toast.error('Failed to create channel');
      console.error('Error creating channel:', error);
    },
  });

  const createProjectMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setIsCreateProjectDialogOpen(false);
      setNewProjectName('');
      setNewProjectDescription('');
      setNewProjectDetails('');
      toast.success('Project created successfully!');
    },
    onError: (error) => {
      toast.error('Failed to create project');
      console.error('Error creating project:', error);
    },
  });

  const handleCreateChannel = (e: React.FormEvent) => {
    e.preventDefault();
    if (newChannelName.trim()) {
      createChannelMutation.mutate({
        name: newChannelName.trim(),
        description: newChannelDescription.trim(),
        projects: selectedProjects,
      });
    }
  };

  const handleProjectToggle = (projectId: number) => {
    setSelectedProjects(prev => 
      prev.includes(projectId) 
        ? prev.filter(id => id !== projectId)
        : [...prev, projectId]
    );
  };

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (newProjectName.trim()) {
      createProjectMutation.mutate({
        name: newProjectName.trim(),
        description: newProjectDescription.trim(),
        details: newProjectDetails.trim(),
      });
    }
  };

  return (
    <aside className="w-64 flex-shrink-0 border-r border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900 flex flex-col justify-between">
      <div>
        <Tabs defaultValue="channels" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="channels" className="flex items-center gap-2">
              <Hash className="h-4 w-4" />
              Channels
            </TabsTrigger>
            <TabsTrigger value="projects" className="flex items-center gap-2">
              <FolderOpen className="h-4 w-4" />
              Projects
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="channels" className="mt-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Channels</h3>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                <Plus className="h-4 w-4" />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Channel</DialogTitle>
                <DialogDescription>
                  Create a new channel for your team to collaborate.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateChannel} className="space-y-4">
                <div>
                  <label htmlFor="channel-name" className="block text-sm font-medium mb-1">
                    Channel Name
                  </label>
                  <Input
                    id="channel-name"
                    value={newChannelName}
                    onChange={(e) => setNewChannelName(e.target.value)}
                    placeholder="e.g., general"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="channel-description" className="block text-sm font-medium mb-1">
                    Description (optional)
                  </label>
                  <Input
                    id="channel-description"
                    value={newChannelDescription}
                    onChange={(e) => setNewChannelDescription(e.target.value)}
                    placeholder="Channel description"
                  />
                </div>
                <div>
                  <Label className="text-sm font-medium mb-2 block">
                    Related Projects (optional)
                  </Label>
                  <div className="max-h-32 overflow-y-auto border rounded-md p-2 space-y-2">
                    {projects && projects.length > 0 ? (
                      projects.map((project) => (
                        <div key={project.id} className="flex items-center space-x-2">
                          <Checkbox
                            id={`project-${project.id}`}
                            checked={selectedProjects.includes(project.id)}
                            onCheckedChange={() => handleProjectToggle(project.id)}
                          />
                          <Label
                            htmlFor={`project-${project.id}`}
                            className="text-sm cursor-pointer flex-1"
                          >
                            {project.name}
                          </Label>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500 text-center py-2">
                        No projects available
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex justify-end space-x-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsCreateDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={createChannelMutation.isPending}
                  >
                    {createChannelMutation.isPending ? 'Creating...' : 'Create Channel'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        <div className="mt-4 space-y-2">
          {isLoading && <p className="text-sm text-gray-500">Loading channels...</p>}
          {error && <p className="text-sm text-red-500">Error fetching channels.</p>}
          {channels && channels.map((channel) => (
            <div 
              key={channel.id} 
              className={`flex items-center space-x-2 text-sm cursor-pointer p-2 rounded transition-colors ${
                selectedChannel?.id === channel.id 
                  ? 'bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100' 
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:hover:text-gray-50 dark:hover:bg-gray-800'
              }`}
              onClick={() => {
                setSelectedChannel(channel);
                setSelectedProject(null); // Clear project selection when channel is selected
                setSelectedBot(null); // Clear bot selection when channel is selected
                setBotViewActive(false); // Deactivate bot view when channel is selected
              }}
            >
              <Hash className="h-4 w-4" />
              <span>{channel.name}</span>
            </div>
          ))}
          {!isLoading && !error && channels?.length === 0 && (
              <p className="text-sm text-gray-500">No channels found. Create one to get started!</p>
          )}
            </div>
          </TabsContent>
          
          <TabsContent value="projects" className="mt-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Projects</h3>
              <Dialog open={isCreateProjectDialogOpen} onOpenChange={setIsCreateProjectDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                    <Plus className="h-4 w-4" />
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Create New Project</DialogTitle>
                    <DialogDescription>
                      Create a new project to organize your work and assets.
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleCreateProject} className="space-y-4">
                    <div>
                      <label htmlFor="project-name" className="block text-sm font-medium mb-1">
                        Project Name
                      </label>
                      <Input
                        id="project-name"
                        value={newProjectName}
                        onChange={(e) => setNewProjectName(e.target.value)}
                        placeholder="e.g., My Software Project"
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="project-description" className="block text-sm font-medium mb-1">
                        Description (optional)
                      </label>
                      <Input
                        id="project-description"
                        value={newProjectDescription}
                        onChange={(e) => setNewProjectDescription(e.target.value)}
                        placeholder="Project description"
                      />
                    </div>
                    <div>
                      <label htmlFor="project-details" className="block text-sm font-medium mb-1">
                        Details (optional)
                      </label>
                      <Input
                        id="project-details"
                        value={newProjectDetails}
                        onChange={(e) => setNewProjectDetails(e.target.value)}
                        placeholder="Project details"
                      />
                    </div>
                    <div className="flex justify-end space-x-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setIsCreateProjectDialogOpen(false)}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        disabled={createProjectMutation.isPending}
                      >
                        {createProjectMutation.isPending ? 'Creating...' : 'Create Project'}
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
            <div className="space-y-2">
              {projects && projects.map((project) => (
                <div 
                  key={project.id} 
                  className={`flex items-center space-x-2 text-sm cursor-pointer p-2 rounded transition-colors ${
                    selectedProject?.id === project.id 
                      ? 'bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100' 
                      : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:hover:text-gray-50 dark:hover:bg-gray-800'
                  }`}
                  onClick={() => {
                    setSelectedProject(project);
                    setSelectedChannel(null); // Clear channel selection when project is selected
                    setSelectedBot(null); // Clear bot selection when project is selected
                    setBotViewActive(false); // Deactivate bot view when project is selected
                  }}
                >
                  <FolderOpen className="h-4 w-4" />
                  <span>{project.name}</span>
                </div>
              ))}
              {projects?.length === 0 && (
                <p className="text-sm text-gray-500">No projects found. Create one to get started!</p>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      <div>
        <div className="border-t border-gray-200 dark:border-gray-800 my-4" />
        <nav className="space-y-2">
          <button 
            onClick={() => {
              setSelectedChannel(null);
              setSelectedProject(null);
              setSelectedBot(null);
              setBotViewActive(true); // Activate bot view
            }}
            className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors w-full text-left ${
              isBotViewActive 
                ? 'bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100' 
                : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-50'
            }`}
          >
            <Bot className="h-4 w-4" />
            My Bots
          </button>
          <Link href="#" className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-50">
            <Settings className="h-4 w-4" />
            Settings
          </Link>
        </nav>
      </div>
    </aside>
  );
}

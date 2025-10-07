"use client";

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, FileText, Image, Link, File, Calendar, User, Edit } from 'lucide-react';
import api from '@/lib/api';
import { useProjectStore, ProjectAsset } from '@/store/projectStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';

const fetchProjectAssets = async (projectId: number): Promise<ProjectAsset[]> => {
  const { data } = await api.get(`/api/projects/${projectId}/assets/`);
  return data;
};

const createProjectAsset = async (projectId: number, assetData: FormData): Promise<ProjectAsset> => {
  const { data } = await api.post(`/api/projects/${projectId}/assets/`, assetData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
};

const updateProject = async (projectId: number, projectData: any): Promise<any> => {
  const { data } = await api.patch(`/api/projects/${projectId}/`, projectData);
  return data;
};

const getAssetIcon = (assetType: string) => {
  switch (assetType) {
    case 'document':
    case 'analysis':
      return <FileText className="h-4 w-4" />;
    case 'image':
      return <Image className="h-4 w-4" />;
    case 'reference':
      return <Link className="h-4 w-4" />;
    default:
      return <File className="h-4 w-4" />;
  }
};

const formatFileSize = (bytes?: number) => {
  if (!bytes) return 'Unknown size';
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('tr-TR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export function ProjectDetail() {
  const [isCreateAssetDialogOpen, setIsCreateAssetDialogOpen] = useState(false);
  const [isEditDetailsOpen, setIsEditDetailsOpen] = useState(false);
  const [editProjectName, setEditProjectName] = useState('');
  const [editProjectDescription, setEditProjectDescription] = useState('');
  const [editProjectDetails, setEditProjectDetails] = useState('');
  const [newAssetName, setNewAssetName] = useState('');
  const [newAssetType, setNewAssetType] = useState('');
  const [newAssetDescription, setNewAssetDescription] = useState('');
  const [newAssetSummary, setNewAssetSummary] = useState('');
  const [newAssetUrl, setNewAssetUrl] = useState('');
  const [newAssetFile, setNewAssetFile] = useState<File | null>(null);
  
  const queryClient = useQueryClient();
  const { selectedProject, setSelectedAsset } = useProjectStore();

  const { data: assets, isLoading } = useQuery<ProjectAsset[]>({
    queryKey: ['project-assets', selectedProject?.id],
    queryFn: () => fetchProjectAssets(selectedProject!.id),
    enabled: !!selectedProject?.id,
  });

  const createAssetMutation = useMutation({
    mutationFn: (assetData: FormData) => createProjectAsset(selectedProject!.id, assetData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-assets', selectedProject?.id] });
      setIsCreateAssetDialogOpen(false);
      setNewAssetName('');
      setNewAssetType('');
      setNewAssetDescription('');
      setNewAssetSummary('');
      setNewAssetUrl('');
      setNewAssetFile(null);
      toast.success('Asset created successfully!');
    },
    onError: (error) => {
      toast.error('Failed to create asset');
      console.error('Error creating asset:', error);
    },
  });

  const updateProjectMutation = useMutation({
    mutationFn: (projectData: any) => updateProject(selectedProject!.id, projectData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setIsEditDetailsOpen(false);
      toast.success('Project updated successfully!');
    },
    onError: (error) => {
      toast.error('Failed to update project');
      console.error('Error updating project:', error);
    },
  });

  const handleCreateAsset = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAssetName.trim() || !newAssetType) {
      toast.error('Please fill in required fields');
      return;
    }

    const formData = new FormData();
    formData.append('name', newAssetName.trim());
    formData.append('asset_type', newAssetType);
    formData.append('description', newAssetDescription.trim());
    formData.append('summary', newAssetSummary.trim());
    
    if (newAssetUrl.trim()) {
      formData.append('url', newAssetUrl.trim());
    }
    
    if (newAssetFile) {
      formData.append('file', newAssetFile);
    }

    createAssetMutation.mutate(formData);
  };

  const handleUpdateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editProjectName.trim()) {
      toast.error('Project name is required');
      return;
    }

    const projectData = {
      name: editProjectName.trim(),
      description: editProjectDescription.trim(),
      details: editProjectDetails.trim(),
    };

    updateProjectMutation.mutate(projectData);
  };

  const handleEditDetailsClick = () => {
    setEditProjectName(selectedProject?.name || '');
    setEditProjectDescription(selectedProject?.description || '');
    setEditProjectDetails(selectedProject?.details || '');
    setIsEditDetailsOpen(true);
  };

  if (!selectedProject) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            No Project Selected
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Select a project from the sidebar to view its details and assets.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Project Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {selectedProject.name}
            </h1>
            {selectedProject.description && (
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {selectedProject.description}
              </p>
            )}
          </div>
          <Button onClick={handleEditDetailsClick}>
            <Edit className="h-4 w-4 mr-2" />
            Edit Details
          </Button>
        </div>
      </div>

      {/* Project Details */}
      {selectedProject.details && (
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Project Details
          </h3>
          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {selectedProject.details}
          </p>
        </div>
      )}

      {/* Assets List */}
      <div className="flex-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Assets ({assets?.length || 0})
          </h3>
          <Dialog open={isCreateAssetDialogOpen} onOpenChange={setIsCreateAssetDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Add Asset
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Add New Asset</DialogTitle>
                <DialogDescription>
                  Add a document, image, or reference link to this project.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateAsset} className="space-y-4">
                <div>
                  <Label htmlFor="asset-name">Asset Name *</Label>
                  <Input
                    id="asset-name"
                    value={newAssetName}
                    onChange={(e) => setNewAssetName(e.target.value)}
                    placeholder="e.g., Project Requirements"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="asset-type">Asset Type *</Label>
                  <Select value={newAssetType} onValueChange={setNewAssetType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select asset type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="document">Document</SelectItem>
                      <SelectItem value="analysis">Analysis Document</SelectItem>
                      <SelectItem value="image">Image/Logo</SelectItem>
                      <SelectItem value="brochure">Brochure</SelectItem>
                      <SelectItem value="reference">Reference Link</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="asset-description">Description</Label>
                  <Textarea
                    id="asset-description"
                    value={newAssetDescription}
                    onChange={(e) => setNewAssetDescription(e.target.value)}
                    placeholder="Asset description"
                  />
                </div>
                <div>
                  <Label htmlFor="asset-summary">Summary (for AI)</Label>
                  <Textarea
                    id="asset-summary"
                    value={newAssetSummary}
                    onChange={(e) => setNewAssetSummary(e.target.value)}
                    placeholder="Brief summary for AI understanding"
                  />
                </div>
                <div>
                  <Label htmlFor="asset-url">URL</Label>
                  <Input
                    id="asset-url"
                    type="url"
                    value={newAssetUrl}
                    onChange={(e) => setNewAssetUrl(e.target.value)}
                    placeholder="https://example.com"
                  />
                </div>
                <div>
                  <Label htmlFor="asset-file">File</Label>
                  <Input
                    id="asset-file"
                    type="file"
                    onChange={(e) => setNewAssetFile(e.target.files?.[0] || null)}
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsCreateAssetDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={createAssetMutation.isPending}
                  >
                    {createAssetMutation.isPending ? 'Adding...' : 'Add Asset'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        
        {isLoading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-500 mt-2">Loading assets...</p>
          </div>
        )}

        {!isLoading && (!assets || assets.length === 0) && (
          <div className="text-center py-8">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">
              No assets yet. Add your first asset to get started.
            </p>
          </div>
        )}

        {!isLoading && assets && assets.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {assets.map((asset) => (
              <div
                key={asset.id}
                className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedAsset(asset)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {getAssetIcon(asset.asset_type)}
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {asset.name}
                    </span>
                  </div>
                </div>
                
                {asset.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                    {asset.description}
                  </p>
                )}
                
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                  <div className="flex items-center space-x-1">
                    <Calendar className="h-3 w-3" />
                    <span>{formatDate(asset.created_at)}</span>
                  </div>
                  {asset.file_size && (
                    <span>{formatFileSize(asset.file_size)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edit Project Details Dialog */}
      <Dialog open={isEditDetailsOpen} onOpenChange={setIsEditDetailsOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Project Details</DialogTitle>
            <DialogDescription>
              Update the project information below.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleUpdateProject} className="space-y-4">
            <div>
              <Label htmlFor="project-name">Project Name *</Label>
              <Input
                id="project-name"
                value={editProjectName}
                onChange={(e) => setEditProjectName(e.target.value)}
                placeholder="Project name"
                required
              />
            </div>
            <div>
              <Label htmlFor="project-description">Description</Label>
              <Textarea
                id="project-description"
                value={editProjectDescription}
                onChange={(e) => setEditProjectDescription(e.target.value)}
                placeholder="Project description"
              />
            </div>
            <div>
              <Label htmlFor="project-details">Details</Label>
              <Textarea
                id="project-details"
                value={editProjectDetails}
                onChange={(e) => setEditProjectDetails(e.target.value)}
                placeholder="Project details"
                rows={4}
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsEditDetailsOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={updateProjectMutation.isPending}
              >
                {updateProjectMutation.isPending ? 'Updating...' : 'Update Project'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

"use client";

import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useQuery } from '@tanstack/react-query';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Bot } from '@/store/botStore';
import api from '@/lib/api';

// Define the schema for the form validation
const formSchema = z.object({
  name: z.string().min(2, { message: "Name must be at least 2 characters." }),
  title: z.string().min(5, { message: "Title must be at least 5 characters." }),
  character: z.string().min(10, { message: "Character description must be at least 10 characters." }),
  job_description: z.string().min(10, { message: "Job description must be at least 10 characters." }),
  llm_provider: z.string().min(1, "Please select a provider."),
  llm_model: z.string().min(1, "Please select a model."),
  temperature: z.number().min(0).max(2),
  color: z.string().regex(/^#[0-9A-F]{6}$/i, "Please select a valid color."),
});

type FormValues = z.infer<typeof formSchema>;

interface LLMProviders {
    [provider: string]: {
        label: string;
        models: string[];
    };
}

interface BotFormProps {
  bot?: Bot | null; // The bot to edit, if any
  onSuccess: () => void; // Callback to run on successful submission
}

// Fetcher function for LLM providers
const fetchProviders = async (): Promise<LLMProviders> => {
    const { data } = await api.get('/api/bots/llm-providers/');
    return data;
};

export const BotForm: React.FC<BotFormProps> = ({ bot, onSuccess }) => {
  const isEditMode = !!bot;

  const { data: providers, isLoading: isLoadingProviders } = useQuery<LLMProviders>({
    queryKey: ['llmProviders'],
    queryFn: fetchProviders,
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: bot?.name || "",
      title: bot?.title || "",
      character: bot?.character || "",
      job_description: bot?.job_description || "",
      llm_provider: bot?.llm_provider || "",
      llm_model: bot?.llm_model || "",
      temperature: bot?.temperature || 0.7,
      color: bot?.color || "#3B82F6",
    },
  });

  const selectedProvider = form.watch('llm_provider');

  useEffect(() => {
    // Reset model when provider changes
    if (!isEditMode) {
        form.resetField('llm_model');
    }
  }, [selectedProvider, form, isEditMode]);

  const onSubmit = async (values: FormValues) => {
    try {
      // Generate system prompt from character and job description
      const systemPrompt = `You are ${values.name}, ${values.title}.

Character: ${values.character}

Job Description: ${values.job_description}

Instructions:
- Stay in character as ${values.name}
- Follow your job description and role
- Be helpful, engaging, and conversational
- Provide thoughtful responses based on your character and expertise
- Challenge ideas when appropriate to find weaknesses or improvements

Remember: You are ${values.name}, not just a generic AI assistant.`;

      const botData = {
        ...values,
        system_prompt: systemPrompt,
      };

      if (isEditMode && bot) {
        // Update existing bot
        await api.put(`/api/bots/${bot.id}/`, botData);
      } else {
        // Create new bot
        await api.post('/api/bots/', botData);
      }
      onSuccess(); // Trigger callback to close modal and refetch list
    } catch (error) {
      console.error("Failed to save bot:", error);
      // Here you would typically show a toast notification
      form.setError("root.serverError", {
          type: "manual",
          message: "An unexpected error occurred. Please try again."
      })
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Bot Name</FormLabel>
              <FormControl>
                <Input placeholder="e.g., Devil's Advocate" {...field} />
              </FormControl>
              <FormDescription>A short, descriptive name for your bot.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Bot Title / Role</FormLabel>
              <FormControl>
                <Input placeholder="e.g., Devil's Advocate, Risk Analyst, Creative Writer" {...field} />
              </FormControl>
              <FormDescription>A brief description of the bot&apos;s role or expertise area.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="character"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Character Description</FormLabel>
              <FormControl>
                <Textarea 
                  placeholder="Describe the bot's personality, background, communication style, and unique traits..."
                  className="min-h-[100px]"
                  {...field} 
                />
              </FormControl>
              <FormDescription>Define the bot&apos;s personality, background, and how they communicate.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="job_description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Job Description & Expertise</FormLabel>
              <FormControl>
                <Textarea 
                  placeholder="Describe what the bot does, their expertise areas, responsibilities, and how they approach problems..."
                  className="min-h-[100px]"
                  {...field} 
                />
              </FormControl>
              <FormDescription>Define the bot&apos;s professional role, expertise, and approach to tasks.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="llm_provider"
          render={({ field }) => (
            <FormItem>
              <FormLabel>LLM Provider</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value} disabled={isLoadingProviders}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a provider..." />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {providers && Object.entries(providers).map(([key, provider]) => (
                    <SelectItem key={key} value={key}>{provider.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="llm_model"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Model</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value} disabled={!selectedProvider}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a model..." />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {selectedProvider && providers?.[selectedProvider]?.models.map((model) => (
                    <SelectItem key={model} value={model}>{model}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormDescription>Select a provider first.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="color"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Bot Color</FormLabel>
              <FormControl>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={field.value}
                      onChange={(e) => field.onChange(e.target.value)}
                      className="w-12 h-8 rounded border border-gray-300 cursor-pointer"
                    />
                    <Input
                      value={field.value}
                      onChange={(e) => field.onChange(e.target.value)}
                      placeholder="#3B82F6"
                      className="w-24"
                    />
                  </div>
                  <div 
                    className="w-8 h-8 rounded-full border-2 border-gray-300 flex items-center justify-center text-white font-semibold text-sm"
                    style={{ backgroundColor: field.value }}
                  >
                    {bot?.name?.charAt(0).toUpperCase() || 'B'}
                  </div>
                </div>
              </FormControl>
              <FormDescription>
                Choose a color for your bot's avatar. This will be displayed in chat and bot lists.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="temperature"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Temperature: {field.value}</FormLabel>
              <FormControl>
                <Slider
                  min={0}
                  max={2}
                  step={0.1}
                  value={[field.value]}
                  onValueChange={(value) => field.onChange(value[0])}
                  className="w-full"
                />
              </FormControl>
              <FormDescription>
                Controls randomness: 0 = deterministic, 2 = very creative. Recommended: 0.7-0.9 for creative bots, 0.3-0.5 for analytical bots.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        {form.formState.errors.root?.serverError && (
            <p className="text-sm font-medium text-destructive">{form.formState.errors.root.serverError.message}</p>
        )}

        <Button type="submit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? 'Saving...' : (isEditMode ? 'Save Changes' : 'Create Bot')}
        </Button>
      </form>
    </Form>
  );
};

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import api from '@/lib/api';

// Define the schema for the form validation
const formSchema = z.object({
  name: z.string().min(2, { message: "Name must be at least 2 characters." }),
  title: z.string().min(5, { message: "Title must be at least 5 characters." }),
  llm_provider: z.string({ required_error: "Please select a provider." }),
  llm_model: z.string({ required_error: "Please select a model." }),
});

type FormValues = z.infer<typeof formSchema>;

// Define the types for the component props
interface Bot {
  id: number;
  name: string;
  title: string;
  llm_provider: string;
  llm_model: string;
}

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
      llm_provider: bot?.llm_provider || "",
      llm_model: bot?.llm_model || "",
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
      if (isEditMode && bot) {
        // Update existing bot
        await api.put(`/api/bots/${bot.id}/`, values);
      } else {
        // Create new bot
        await api.post('/api/bots/', values);
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
              <FormLabel>Bot Title / Persona</FormLabel>
              <FormControl>
                <Input placeholder="e.g., Challenges ideas to find weaknesses" {...field} />
              </FormControl>
              <FormDescription>A brief description of the bot's role or personality.</FormDescription>
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

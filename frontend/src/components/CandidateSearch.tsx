"use client";

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Search, Github, FileText, Camera } from 'lucide-react';
import { toast } from 'sonner';

export interface Candidate {
  id: string;
  name: string;
  title: string;
  location: string;
  github?: string;
  linkedin?: string;
  instagram?: string;
  avatar: string;
  skills: string[];
  experience: string;
  matchScore: number;
}

const API_BASE_URL = "http://localhost:8000"; // Your backend API base URL
const API_KEY = "your_api_key_here"; // Replace with your actual API Key

const CandidateSearch = ({
  onCandidateSelect
}: { onCandidateSelect: (candidate: Candidate) => void }) => {
  const [searchData, setSearchData] = useState({
    githubUsername: '',
    linkedinUrl: '',
    instagramHandle: '',
    resumeFile: null as File | null
  });
  const [isSearching, setIsSearching] = useState(false);
  
  const handleSearch = async () => {
    if (!searchData.githubUsername && !searchData.linkedinUrl && !searchData.instagramHandle && !searchData.resumeFile) {
      toast.error("Please provide at least one candidate data source.", {
        description: "Input Required",
      });
      return;
    }
    setIsSearching(true);

    let foundCandidate: Partial<Candidate> = {
      id: '1',
      name: 'Candidate',
      title: 'Unknown',
      location: 'Unknown',
      avatar: 'https://via.placeholder.com/150',
      skills: [],
      experience: 'N/A',
      matchScore: 0
    };

    try {
      // GitHub Search
      if (searchData.githubUsername) {
        const response = await fetch(`${API_BASE_URL}/github/${searchData.githubUsername}`, {
          headers: {
            'X-API-Key': API_KEY,
          },
        });
        if (response.ok) {
          const data = await response.json();
          foundCandidate.github = data.html_url || data.url;
          foundCandidate.name = data.name || foundCandidate.name;
          foundCandidate.avatar = data.avatar_url || foundCandidate.avatar;
          toast.success(`GitHub profile for ${searchData.githubUsername} fetched successfully.`, { description: "GitHub Data" });
        } else {
          const errorData = await response.json();
          toast.error(`Failed to fetch GitHub profile: ${errorData.detail || response.statusText}`, { description: "GitHub Data Error" });
        }
      }

      // Portfolio (LinkedIn) Search
      if (searchData.linkedinUrl) {
        const formData = new FormData();
        // Assuming backend expects a file upload or similar for linkedin/portfolio
        // For now, let's just make a GET request to a simplified /portfolio endpoint if it exists
        // Based on README, it's GET /portfolio?url={url}
        const response = await fetch(`${API_BASE_URL}/portfolio?url=${encodeURIComponent(searchData.linkedinUrl)}`, {
          headers: {
            'X-API-Key': API_KEY,
          },
        });
        if (response.ok) {
          const data = await response.json();
          foundCandidate.linkedin = searchData.linkedinUrl;
          // You would parse data to update candidate fields
          toast.success(`Portfolio URL ${searchData.linkedinUrl} analyzed successfully.`, { description: "Portfolio Data" });
        } else {
          const errorData = await response.json();
          toast.error(`Failed to analyze portfolio: ${errorData.detail || response.statusText}`, { description: "Portfolio Data Error" });
        }
      }

      // Instagram Search
      if (searchData.instagramHandle) {
        const response = await fetch(`${API_BASE_URL}/instagram/${searchData.instagramHandle}`, {
          headers: {
            'X-API-Key': API_KEY,
          },
        });
        if (response.ok) {
          const data = await response.json();
          foundCandidate.instagram = data.username;
          foundCandidate.avatar = data.profile_pic_url || foundCandidate.avatar;
          // You would parse data to update candidate fields
          toast.success(`Instagram profile for ${searchData.instagramHandle} fetched successfully.`, { description: "Instagram Data" });
        } else {
          const errorData = await response.json();
          toast.error(`Failed to fetch Instagram profile: ${errorData.detail || response.statusText}`, { description: "Instagram Data Error" });
        }
      }

      // Resume Upload
      if (searchData.resumeFile) {
        const formData = new FormData();
        formData.append('file', searchData.resumeFile);
        const response = await fetch(`${API_BASE_URL}/resume/upload`, {
          method: 'POST',
          headers: {
            'X-API-Key': API_KEY,
          },
          body: formData,
        });
        if (response.ok) {
          const data = await response.json();
          // You would parse data to update candidate fields based on resume analysis
          toast.success(`Resume uploaded and analyzed successfully.`, { description: "Resume Data" });
        } else {
          const errorData = await response.json();
          toast.error(`Failed to upload or analyze resume: ${errorData.detail || response.statusText}`, { description: "Resume Data Error" });
        }
      }

      // After all attempts, notify the parent component with the (potentially partial) candidate data
      onCandidateSelect(foundCandidate as Candidate);
      toast.success("Candidate analysis process completed.", { description: "Analysis Complete" });

    } catch (error) {
      console.error("API call error:", error);
      toast.error(`An unexpected error occurred during search: ${(error as Error).message}`, { description: "Search Error" });
    } finally {
      setIsSearching(false);
    }
  };
  const recentSearches = [{
    name: 'Alex Chen',
    title: 'Full Stack Developer',
    matchScore: 88
  }, {
    name: 'Maria Garcia',
    title: 'Data Scientist',
    matchScore: 95
  }, {
    name: 'David Kim',
    title: 'DevOps Engineer',
    matchScore: 82
  }];
  return <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <Card className="bg-white/60 backdrop-blur-sm border-white/20 shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Search className="w-5 h-5 text-blue-600" />
              <span>Find Candidate</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="github" className="flex items-center space-x-2">
                  <Github className="w-4 h-4" />
                  <span>GitHub Username</span>
                </Label>
                <Input id="github" placeholder="e.g. octocat" value={searchData.githubUsername} onChange={e => setSearchData({
                ...searchData,
                githubUsername: e.target.value
              })} className="bg-white/80" />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="linkedin" className="flex items-center space-x-2">
                  <FileText className="w-4 h-4" />
                  <span>Portfolio URL</span>
                </Label>
                <Input id="linkedin" placeholder="https://yourportfolio.com" value={searchData.linkedinUrl} onChange={e => setSearchData({
                ...searchData,
                linkedinUrl: e.target.value
              })} className="bg-white/80" />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="instagram" className="flex items-center space-x-2">
                  <Camera className="w-4 h-4" />
                  <span>Instagram Handle</span>
                </Label>
                <Input id="instagram" placeholder="@username" value={searchData.instagramHandle} onChange={e => setSearchData({
                ...searchData,
                instagramHandle: e.target.value
              })} className="bg-white/80" />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="resume">Resume Upload</Label>
                <Input id="resume" type="file" accept=".pdf,.doc,.docx" onChange={e => setSearchData({
                ...searchData,
                resumeFile: e.target.files?.[0] || null
              })} className="bg-white/80" />
              </div>
            </div>
            
            <Button onClick={handleSearch} disabled={isSearching} className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white">
              {isSearching ? 'Analyzing Candidate...' : 'Search & Analyze'}
            </Button>
          </CardContent>
        </Card>
      </div>

      <div>
        <Card className="bg-white/60 backdrop-blur-sm border-white/20 shadow-xl">
          <CardHeader>
            <CardTitle className="text-lg">Recent Searches</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {recentSearches.map((candidate, index) => <div key={index} className="p-3 rounded-lg bg-white/40 hover:bg-white/60 transition-colors cursor-pointer">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-sm">{candidate.name}</p>
                    <p className="text-xs text-muted-foreground">{candidate.title}</p>
                  </div>
                  <Badge variant={candidate.matchScore > 90 ? 'default' : 'secondary'} className="text-xs">
                    {candidate.matchScore}%
                  </Badge>
                </div>
              </div>)}
          </CardContent>
        </Card>
      </div>
    </div>;
};
export default CandidateSearch; 
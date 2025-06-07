"use client";

import CandidateSearch from '@/components/CandidateSearch';

export default function Home() {
  return (
    <div className="min-h-screen p-8">
      <CandidateSearch onCandidateSelect={(candidate) => console.log('Candidate Selected:', candidate)} />
    </div>
  );
}

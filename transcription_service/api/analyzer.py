#!/usr/bin/env python3
"""
Transcript analysis module.
Refactored from the original analyze_transcript.py script.
Generates summaries and extracts key insights from transcripts.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TranscriptAnalyzer:
    """Analyzes transcripts to extract themes, insights, and summaries."""

    def __init__(self):
        """Initialize the analyzer with predefined themes."""
        self.themes = {
            "Education vs Experience": [],
            "Student Dropout Rates": [],
            "Industry Compensation": [],
            "Hands-on Training": [],
            "Assessment and Certification": [],
            "Employer Expectations": [],
            "Resources and Equipment": [],
            "Job Placement": [],
            "Industry Challenges": []
        }

    def analyze(self, transcript_text):
        """
        Analyze a transcript and generate a comprehensive summary.

        Args:
            transcript_text: Full transcript as string

        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info("Analyzing transcript...")

            # Reset themes for new analysis
            for key in self.themes:
                self.themes[key] = []

            # Split into sentences for analysis
            sentences = [s.strip() for s in transcript_text.split('.') if s.strip()]

            # Categorize sentences by theme
            self._categorize_sentences(sentences)

            # Generate summary structure
            summary = self._generate_summary(transcript_text)

            logger.info("Analysis completed successfully")
            return summary

        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            return None

    def _categorize_sentences(self, sentences):
        """Categorize sentences into themes based on keywords."""
        for sentence in sentences:
            sentence_lower = sentence.lower()

            # Education and programs
            if any(keyword in sentence_lower for keyword in ['education', 'school', 'college', 'program']):
                if 'dropout' in sentence_lower or 'drop out' in sentence_lower:
                    self.themes["Student Dropout Rates"].append(sentence)
                else:
                    self.themes["Education vs Experience"].append(sentence)

            # Compensation and pay
            elif any(keyword in sentence_lower for keyword in ['flat rate', 'compensation', 'pay', 'salary', 'wage']):
                self.themes["Industry Compensation"].append(sentence)

            # Hands-on training
            elif any(keyword in sentence_lower for keyword in ['hands on', 'hands-on', 'practice', 'lab', 'vehicle']):
                self.themes["Hands-on Training"].append(sentence)

            # Assessment
            elif any(keyword in sentence_lower for keyword in ['assessment', 'test', 'certification', 'grade', 'gpa']):
                self.themes["Assessment and Certification"].append(sentence)

            # Employers
            elif any(keyword in sentence_lower for keyword in ['employer', 'dealership', 'shop', 'hire', 'hiring']):
                self.themes["Employer Expectations"].append(sentence)

            # Resources
            elif any(keyword in sentence_lower for keyword in ['equipment', 'tools', 'resources', 'budget']):
                self.themes["Resources and Equipment"].append(sentence)

            # Job placement
            elif any(keyword in sentence_lower for keyword in ['graduate', 'job', 'placement', 'career']):
                self.themes["Job Placement"].append(sentence)

    def _generate_summary(self, full_text):
        """Generate structured summary from analysis."""
        summary = {
            "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "transcript_length": len(full_text),
            "main_topics": {},
            "key_insights": [],
            "statistics_mentioned": [],
        }

        # Process themes with content
        for theme, content in self.themes.items():
            if content:
                summary["main_topics"][theme] = {
                    "key_points": content[:5],  # Top 5 relevant sentences
                    "discussion_length": len(content)
                }

        # Generate key insights (these are generic - could be enhanced with NLP)
        if summary["main_topics"]:
            summary["key_insights"] = self._extract_insights()

        return summary

    def _extract_insights(self):
        """
        Extract key insights based on identified themes.
        This is a simplified version - could be enhanced with NLP.
        """
        insights = []

        if self.themes["Education vs Experience"]:
            insights.append("Discussion includes formal education and its role in professional development")

        if self.themes["Student Dropout Rates"]:
            insights.append("Student retention and dropout rates are significant concerns")

        if self.themes["Industry Compensation"]:
            insights.append("Compensation models and payment structures are discussed")

        if self.themes["Hands-on Training"]:
            insights.append("Practical, hands-on training is emphasized as important")

        if self.themes["Assessment and Certification"]:
            insights.append("Assessment methods and certification standards are addressed")

        if self.themes["Employer Expectations"]:
            insights.append("Gap between education outcomes and employer needs is highlighted")

        if self.themes["Resources and Equipment"]:
            insights.append("Resource availability and equipment access are key challenges")

        if self.themes["Job Placement"]:
            insights.append("Career placement and job opportunities are discussed")

        return insights

    def format_summary_markdown(self, summary):
        """
        Format analysis summary as Markdown.

        Args:
            summary: Summary dictionary from analyze()

        Returns:
            Formatted markdown string
        """
        if not summary:
            return "Analysis failed"

        md_output = "# Transcript Analysis Summary\n\n"
        md_output += f"**Analysis Date:** {summary['analysis_date']}\n"
        md_output += f"**Transcript Length:** {summary['transcript_length']} characters\n\n"

        # Main topics
        if summary['main_topics']:
            md_output += "## Main Topics Discussed\n\n"
            for topic, details in summary['main_topics'].items():
                md_output += f"### {topic}\n"
                md_output += f"**Discussion Points:** {details['discussion_length']} relevant segments\n\n"
                md_output += "**Key Quotes:**\n"
                for point in details['key_points']:
                    md_output += f"- {point}\n"
                md_output += "\n"

        # Key insights
        if summary['key_insights']:
            md_output += "## Key Insights\n\n"
            for i, insight in enumerate(summary['key_insights'], 1):
                md_output += f"{i}. {insight}\n"
            md_output += "\n"

        return md_output

    def get_short_summary(self, summary):
        """
        Generate a short summary suitable for Coda table display.

        Args:
            summary: Summary dictionary from analyze()

        Returns:
            Concise summary string
        """
        if not summary or not summary.get('main_topics'):
            return "No significant topics identified"

        topics = list(summary['main_topics'].keys())
        insights = summary.get('key_insights', [])

        short = f"Topics: {', '.join(topics[:3])}"
        if len(topics) > 3:
            short += f" (+{len(topics)-3} more)"

        if insights:
            short += f"\n\nKey Insights:\n"
            for i, insight in enumerate(insights[:3], 1):
                short += f"{i}. {insight}\n"

        return short


if __name__ == "__main__":
    # Test the analyzer
    logging.basicConfig(level=logging.INFO)

    test_text = input("Enter some text to analyze (or press Enter for sample): ")

    if not test_text:
        test_text = """
        The automotive education program faces challenges with student dropout rates around 30%.
        Many students struggle with hands-on training due to limited equipment resources.
        Employers expect graduates to have practical experience, but schools lack sufficient vehicles.
        The flat rate compensation system makes it difficult to attract new technicians.
        Assessment and certification standards need improvement to better demonstrate student capabilities.
        """

    analyzer = TranscriptAnalyzer()
    result = analyzer.analyze(test_text)

    if result:
        print("\n--- ANALYSIS RESULT ---")
        print(f"Topics found: {len(result['main_topics'])}")
        print(f"Insights: {len(result['key_insights'])}")
        print("\nShort Summary:")
        print(analyzer.get_short_summary(result))
        print("\n✓ Analysis successful")
    else:
        print("✗ Analysis failed")

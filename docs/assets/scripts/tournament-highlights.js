// Fetch the JSON report and generate both the summary and the top players table
fetch('last_weekend_report.json')
    .then(response => response.json())
    .then(data => {
        // --- Existing Summary Code ---
        const {
            team_score_recent,
            team_score_recent_rank,
            team_score_previous,
            team_score_previous_rank,
            team_score_max,
            team_score_max_rank,
            percent_change_previous
        } = data;

        // Format numbers with locale separators
        const recentScore = team_score_recent.toLocaleString();
        const previousScore = team_score_previous.toLocaleString();
        const maxScore = team_score_max.toLocaleString();

        // Map rank strings to medal emojis
        const rankEmojis = {
            "#1": "🥇",
            "#2": "🥈",
            "#3": "🥉"
        };

        // Tournament rank header (moved to its own header)
        const tournamentHeader = `<h2 class="text-xl font-bold mb-4">
    Tournament Rank: ${team_score_recent_rank} ${rankEmojis[team_score_recent_rank] || ''}
  </h2>`;

        // Build score summary sentences as bullet points
        const scoreSentences = [];
        if (team_score_recent >= team_score_max) {
            if (team_score_recent > team_score_max) {
                scoreSentences.push(`This weekend's team score of ${recentScore} is a new record 🏆, surpassing our previous high of ${maxScore}.`);
            } else {
                scoreSentences.push(`This weekend's team score of ${recentScore} ties our previous high of ${maxScore}.`);
            }
        } else {
            scoreSentences.push(`This weekend's team score of ${recentScore} did not beat our highest score of ${maxScore}.`);
        }

        const diff = team_score_recent - team_score_previous;
        if (diff > 0) {
            scoreSentences.push(`We improved from last week's score of ${previousScore} by ${diff.toLocaleString()} points ⬆️.`);
        } else if (diff < 0) {
            scoreSentences.push(`Our score dropped from last week's ${previousScore} by ${Math.abs(diff).toLocaleString()} points ⬇️.`);
        } else {
            scoreSentences.push(`Our score remains the same as last week's ${previousScore}.`);
        }

        if (percent_change_previous > 0) {
            scoreSentences.push(`That's a ${percent_change_previous}% increase ⬆️ compared to our last performance.`);
        } else if (percent_change_previous < 0) {
            scoreSentences.push(`That's a ${Math.abs(percent_change_previous)}% decrease ⬇️ compared to our last performance.`);
        }

        // Build rank details as bullet points
        const rankSentences = [];
        rankSentences.push(`In the previous tournament, our rank was ${team_score_previous_rank} ${rankEmojis[team_score_previous_rank] || ''}.`);
        rankSentences.push(`Our previous high score was achieved at rank ${team_score_max_rank} ${rankEmojis[team_score_max_rank] || ''}.`);

        // Convert sentences arrays to bullet point lists
        const scoreListItems = scoreSentences.map(sentence => `<li>${sentence}</li>`).join('');
        const rankListItems = rankSentences.map(sentence => `<li>${sentence}</li>`).join('');

        // Combine summary HTML
        const summaryHTML = `
    ${tournamentHeader}
    <ul class="list-disc pl-5 mb-4">
      ${scoreListItems}
    </ul>
    <div style="page-break-after: always;"></div>
    <ul class="list-disc pl-5">
      ${rankListItems}
    </ul>
  `;

        document.getElementById('summary').innerHTML = summaryHTML;

        // --- Top Three Players Table ---
        const topPlayers = data.top_three_players;
        let tableHTML = `<h3 class="text-xl font-bold mb-4">The Top Three!</h3>`;
        tableHTML += `<table class="w-full border-collapse">`;

        // For each player, add a table row with:
        // 1. A large emoji for placement
        // 2. The player's tag (left-justified)
        // 3. Their score (right-justified, formatted with locale separators)
        topPlayers.forEach(player => {
            let placementEmoji = "";
            if (player.weekend_rank === 1) {
                placementEmoji = "🥇";
            } else if (player.weekend_rank === 2) {
                placementEmoji = "🥈";
            } else if (player.weekend_rank === 3) {
                placementEmoji = "🥉";
            }

            tableHTML += `
      <tr class="border-t">
        <td class="py-2 text-2xl">${placementEmoji}</td>
        <td class="py-2 text-left">${player.player_tag}</td>
        <td class="py-2 text-right">${player.recent_score.toLocaleString()}</td>
      </tr>`;
        });

        tableHTML += `</table>`;
        document.getElementById('top-players').innerHTML = tableHTML;
    })
    .catch(error => {
        console.error('Error fetching the report:', error);
    });

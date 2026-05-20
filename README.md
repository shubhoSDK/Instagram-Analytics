Instagram-Analytics
End-to-end data cleaning and analysis of a messy real-world  Instagram dataset covering 6 accounts, 668 posts, 60 campaigns,  and 866 conversion events across 5 data sheets.
Dataset Structure
| Sheet | Rows | Description |
|---|---|---|
| Posts_Raw | 668 | One row per Instagram post |
| Campaigns | 60 | One row per paid campaign |
| Conversions_Orders | 866 | One row per sale/order |
| Daily_Profile_Metrics | 653 | One row per account per day |
| Audience_Survey | 350 | One row per survey response |

Data Issues Fixed
- Removed 72 duplicate rows across all sheets
- Fixed text in numeric columns (Budget = 'TBD', Followers = 'missing')
- Standardised 10 inconsistent Content_Type labels ('REELS'→'Reel')
- Removed 14 negative revenue rows and 11 impossible Reach > Impressions
- Fixed 207 conflicting rows across Payment_Status and Refund_Flag
- Removed 3 campaigns with End_Date before Start_Date

Key Insights
| # | Insight | Finding |
|---|---|---|
| 1 | Best content for engagement | Carousel (6.18% ER) |
| 2 | Best content for reach | Reel (24,726 avg reach) |
| 3 | Best posting hour | 8AM |
| 4 | Best posting day | Wednesday |
| 5 | Hashtag sweet spot | 11–15 tags |
| 6 | Top revenue UTM source | Bio link (₹2.16L) beats paid social |
| 7 | Best campaign ROAS | CAM-2511-025 at 5.19x |
| 8 | Algorithm change impact | Follower gain drops from 217 → 24 on change days |

Tools Used
- Python 3.x
- pandas
- numpy
- openpyxl

How to Run
```bash
Install dependencies
pip install -r requirements.txt

Run analysis
python instagram_analysis_v2.py
```

Concepts Covered
- Multi-sheet Excel loading
- Data auditing before cleaning
- Deduplication, type fixing, label standardisation
- Boolean filtering with chained conditions
- Handling conflicting columns (Payment_Status + Refund_Flag)
- KPI derivation: Engagement Rate, ROAS, Saves Rate
- GroupBy + aggregation for segment analysis
- Left joins using merge()

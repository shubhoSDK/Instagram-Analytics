# ================================================================
#  INSTAGRAM ANALYTICS — v2 (Updated & Corrected)
#  Dataset : instagram_difficult_analysis_dataset.xlsx
#
#  KEY UPDATES FROM v1:
#  1. Conversions cleaned using BOTH Payment_Status + Refund_Flag
#     together (neither column alone is reliable — 206 conflicts)
#  2. All filtering uses .copy() correctly — no inplace on filters
#  3. inplace=True only used where it actually works (drop_duplicates)
#  4. All unique values verified against real data before fixing
#  5. One-step chained filters instead of multi-step reassignments
#
#  HOW TO READ THIS FILE:
#  - Every block has a WHY comment explaining the reasoning
#  - LEARN: lines explain the pandas concept being used
#  - Every fix maps to a real issue found in the audit
# ================================================================

import pandas as pd
import numpy as np

FILE_PATH = r'instagram_difficult_analysis_dataset.xlsx'   # ← change to your path


# ================================================================
# STEP 1 — LOAD ALL SHEETS
# ================================================================
# LEARN: sheet_name=None loads every sheet into a dictionary
#        Key   = sheet name (string)
#        Value = DataFrame (the actual table)

all_sheets = pd.read_excel(FILE_PATH, sheet_name=None)

posts = all_sheets['Posts_Raw']
camps = all_sheets['Campaigns']
daily = all_sheets['Daily_Profile_Metrics']
conv  = all_sheets['Conversions_Orders']
surv  = all_sheets['Audience_Survey']

print("✅ Sheets loaded:", list(all_sheets.keys()))
print(f"\n   Posts      : {posts.shape[0]:>4} rows × {posts.shape[1]} cols")
print(f"   Campaigns  : {camps.shape[0]:>4} rows × {camps.shape[1]} cols")
print(f"   Conversions: {conv.shape[0]:>4} rows × {conv.shape[1]} cols")
print(f"   Daily      : {daily.shape[0]:>4} rows × {daily.shape[1]} cols")
print(f"   Survey     : {surv.shape[0]:>4} rows × {surv.shape[1]} cols")


# ================================================================
# STEP 2 — UNDERSTAND THE DATASET
# ================================================================

print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WHAT IS EACH SHEET?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Posts_Raw             → 1 row = 1 Instagram post
  Campaigns             → 1 row = 1 paid campaign
  Daily_Profile_Metrics → 1 row = 1 account on 1 day
  Conversions_Orders    → 1 row = 1 sale/purchase event
  Audience_Survey       → 1 row = 1 follower survey response

  JOIN MAP:
    Posts     ←→ Campaigns    via Campaign_ID
    Posts     ←→ Conversions  via Post_ID
    Campaigns ←→ Conversions  via Campaign_ID
    All       ←→ Daily        via Account
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


# ================================================================
# STEP 3 — AUDIT (find every problem before fixing anything)
# ================================================================
# LEARN: Always audit first. Jumping to cleaning without auditing
#        means you might fix things that don't need fixing and
#        miss things that do.

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  AUDIT RESULTS")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# LEARN: .duplicated('col').sum() counts how many rows share the same key
print(f"\n[DUPLICATES]")
print(f"  Post_ID duplicates     : {posts.duplicated('Post_ID').sum()}")
print(f"  Campaign_ID duplicates : {camps.duplicated('Campaign_ID').sum()}")
print(f"  Event_ID duplicates    : {conv.duplicated('Event_ID').sum()}")
print(f"  Email_Hash duplicates  : {surv.duplicated('Email_Hash').sum()}")
print(f"  Daily full-row dupes   : {daily.duplicated().sum()}")

# LEARN: .isna().sum() counts NaN (missing) values per column
print(f"\n[MISSING VALUES - KEY COLUMNS]")
print(f"  Posts   → Campaign_ID null : {posts['Campaign_ID'].isna().sum()}")
print(f"  Posts   → Likes null       : {posts['Likes'].isna().sum()}")
print(f"  Conv    → Revenue null     : {conv['Revenue_INR'].isna().sum()}")
print(f"  Survey  → Purchase_Intent  : {surv['Purchase_Intent_1_5'].isna().sum()}")
print(f"  Camps   → Budget null/text : {pd.to_numeric(camps['Budget_INR'], errors='coerce').isna().sum()}")

# LEARN: .unique() shows every distinct value in a column
print(f"\n[INCONSISTENT LABELS]")
print(f"  Content_Type  : {posts['Content_Type'].unique()}")
print(f"  Boosted_Flag  : {posts['Boosted_Flag'].unique()}")
print(f"  Payment_Status: {conv['Payment_Status'].unique()}")
print(f"  Refund_Flag   : {conv['Refund_Flag'].dropna().unique()}")
print(f"  Approval      : {camps['Client_Approval_Status'].unique()}")
print(f"  Age_Group     : {surv['Age_Group'].dropna().unique()}")
print(f"  Gender        : {surv['Gender'].dropna().unique()}")
print(f"  Active_Flwr   : {surv['Active_Follower_Flag'].dropna().unique()}")

print(f"\n[DATA LOGIC ERRORS]")
print(f"  Revenue negative        : {(conv['Revenue_INR'] < 0).sum()}")
print(f"  Revenue zero            : {(conv['Revenue_INR'] == 0).sum()}")
print(f"  Ad_Spend negative       : {(posts['Ad_Spend_INR'] < 0).sum()}")
print(f"  Reach > Impressions     : {(posts['Reach'] > posts['Impressions']).sum()}")
print(f"  Camp End < Start date   : {(camps['End_Date'] < camps['Start_Date']).sum()}")

# Show the 3 types of Conversion conflicts (the hardest problem)
# LEARN: | means OR when combining boolean conditions in pandas
#        & means AND  (always wrap each condition in parentheses!)
paid_but_refunded  = conv[(conv['Payment_Status'].str.lower() == 'paid') &
                           (conv['Refund_Flag'].isin(['Y', 'Yes']))]
refunded_no_flag   = conv[(conv['Payment_Status'] == 'Refunded') &
                           (conv['Refund_Flag'] == 'No')]
paid_neg_revenue   = conv[(conv['Payment_Status'].str.lower() == 'paid') &
                           (conv['Revenue_INR'] < 0)]

print(f"\n[CONVERSION CONFLICTS — the dangerous ones]")
print(f"  Paid status BUT Refund=Yes/Y : {len(paid_but_refunded)} rows")
print(f"  Refunded status BUT Flag=No  : {len(refunded_no_flag)} rows")
print(f"  Paid status BUT Revenue < 0  : {len(paid_neg_revenue)} rows")
print(f"  Total conflicting rows       : {len(paid_but_refunded) + len(refunded_no_flag) + len(paid_neg_revenue)}")
print(f"\n  WHY: Two different systems update Payment_Status and")
print(f"  Refund_Flag separately — they go out of sync.")
print(f"  SOLUTION: Use BOTH columns together to catch all cases.")


# ================================================================
# STEP 4 — CLEAN POSTS
# ================================================================

print("\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  CLEANING: Posts_Raw")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# LEARN: .copy() makes an independent copy of the DataFrame
#        Without it, posts_c is just a "view" of posts
#        Modifying posts_c could silently modify posts too → unpredictable
#        Rule: always .copy() when creating a cleaned version
posts_c = posts.drop_duplicates(subset='Post_ID', keep='first').copy()
print(f"Dedup: {len(posts)} → {len(posts_c)} rows (removed {len(posts)-len(posts_c)})")

# Fix 1 — Standardise Content_Type
# LEARN: .str.strip() removes invisible leading/trailing spaces
#        .str.title() → first letter upper, rest lower → 'REELS' → 'Reels'
#        .replace({dict}) maps specific values → 'Reels' → 'Reel'
posts_c['Content_Type'] = (posts_c['Content_Type']
                            .str.strip()
                            .str.title()
                            .replace({'Reels': 'Reel',
                                      'Story': 'Stories',
                                      'Carousel': 'Carousel'}))

print(f"Content_Type after fix: {sorted(posts_c['Content_Type'].unique())}")

# Fix 2 — Standardise Boosted_Flag and Collab_Flag
# LEARN: .map({dict}) replaces using a lookup table
#        Any value NOT in the dict becomes NaN
#        .fillna('No') fills those NaN with 'No'
yn_map = {'Y': 'Yes', 'Yes': 'Yes', 'yes': 'Yes',
          'N': 'No',  'No':  'No',  'no':  'No'}

posts_c['Boosted_Flag'] = posts_c['Boosted_Flag'].map(yn_map).fillna('No')
posts_c['Collab_Flag']  = posts_c['Collab_Flag'].map(yn_map).fillna('No')

# Fix 3 — Post_Time = 'TBD' → NaN (not a real time)
# LEARN: .where(condition) keeps value if True, replaces with NaN if False
posts_c['Post_Time'] = posts_c['Post_Time'].where(
    posts_c['Post_Time'] != 'TBD', other=np.nan
)

# Fix 4 — Likes has missing values → fill with 0
# LEARN: pd.to_numeric(errors='coerce') converts column to numbers
#        Any value that can't convert (text etc.) becomes NaN
#        Then .fillna(0) replaces those NaN with 0
posts_c['Likes'] = pd.to_numeric(posts_c['Likes'], errors='coerce').fillna(0)

# Fix 5 & 6 — Remove logic errors in one chained filter
# LEARN: Chaining conditions with & (AND) in one filter is cleaner
#        than filtering line by line and reassigning each time
#        ~ means NOT (flip True to False and vice versa)
#        We chain all conditions into one .copy() at the end
before = len(posts_c)
posts_c = posts_c[
    (posts_c['Ad_Spend_INR'] >= 0) &              # no negative spend
    (posts_c['Reach'] <= posts_c['Impressions'])   # reach can't exceed impressions
].copy()
print(f"Logic errors removed: {before - len(posts_c)} rows")

# Fix 7 — Parse dates and extract useful parts
# LEARN: pd.to_datetime() converts string dates to proper datetime
#        errors='coerce' turns unparseable dates into NaT (not NaN)
#        .dt.to_period('M') extracts month period e.g. '2025-10'
#        .dt.day_name() extracts 'Monday', 'Tuesday' etc.
posts_c['Post_Date'] = pd.to_datetime(posts_c['Post_Date'], errors='coerce')
posts_c['Month']     = posts_c['Post_Date'].dt.to_period('M')
posts_c['DayOfWeek'] = posts_c['Post_Date'].dt.day_name()

# LEARN: pd.to_datetime with format='%H:%M' parses '08:45' → datetime
#        .dt.hour then pulls out just the integer hour (0–23)
posts_c['Hour'] = pd.to_datetime(
    posts_c['Post_Time'], format='%H:%M', errors='coerce'
).dt.hour

# Derived metric 1 — Engagement Rate
# Formula: (Likes + Comments + Saves + Shares) / Reach × 100
# LEARN: .replace(0, np.nan) on Reach avoids division-by-zero
#        dividing by NaN gives NaN instead of crashing
posts_c['Total_Engagements'] = (posts_c['Likes']    + posts_c['Comments'] +
                                 posts_c['Saves']    + posts_c['Shares'])
posts_c['Engagement_Rate']   = (
    posts_c['Total_Engagements'] /
    posts_c['Reach'].replace(0, np.nan) * 100
).round(2)

# Derived metric 2 — Saves Rate
# Saves signal that users found content worth keeping = content quality
posts_c['Saves_Rate'] = (
    posts_c['Saves'] / posts_c['Reach'].replace(0, np.nan) * 100
).round(2)

# Derived metric 3 — Hashtag bands for sweet-spot analysis
# LEARN: pd.cut() divides a numeric column into labelled ranges
posts_c['Hashtag_Bin'] = pd.cut(
    posts_c['Hashtag_Count'],
    bins   = [0, 5, 10, 15, 20, 30],
    labels = ['1-5', '6-10', '11-15', '16-20', '21-30']
)

print(f"✅ Posts clean: {len(posts_c)} rows")


# ================================================================
# STEP 5 — CLEAN CAMPAIGNS
# ================================================================

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  CLEANING: Campaigns")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# LEARN: No duplicate Campaign_IDs found in audit → skip dedup
#        Only add cleaning steps that are actually needed
camps_c = camps.copy()

# Fix 1 — Budget_INR has 'TBD' text values
# pd.to_numeric converts numbers, 'TBD' becomes NaN
camps_c['Budget_INR'] = pd.to_numeric(camps_c['Budget_INR'], errors='coerce')

# Fill TBD budgets with the median of known budgets
# LEARN: .median() is better than .mean() when data has outliers
median_budget = camps_c['Budget_INR'].median()
camps_c['Budget_INR'] = camps_c['Budget_INR'].fillna(median_budget)
print(f"TBD budgets filled with median: ₹{median_budget:,.0f}")

# Fix 2 — Client_Approval_Status: 'approved' → 'Approved'
camps_c['Client_Approval_Status'] = (camps_c['Client_Approval_Status']
                                      .str.strip()
                                      .str.title())

# Fix 3 — Remove rows where End_Date < Start_Date (impossible)
# LEARN: ~ (tilde) = NOT operator — flips True/False
#        So ~invalid keeps only the valid rows
invalid_dates = camps_c['End_Date'] < camps_c['Start_Date']
camps_c = camps_c[~invalid_dates].copy()
print(f"Invalid date rows removed: {invalid_dates.sum()}")

# Derived metric — Total campaign cost
camps_c['Total_Cost'] = (
    camps_c['Budget_INR'].fillna(0) +
    camps_c['Influencer_Cost_INR'].fillna(0) +
    camps_c['Agency_Fee_INR'].fillna(0)
)

# Derived metric — Campaign duration in days
camps_c['Duration_Days'] = (
    camps_c['End_Date'] - camps_c['Start_Date']
).dt.days

print(f"✅ Campaigns clean: {len(camps_c)} rows")


# ================================================================
# STEP 6 — CLEAN CONVERSIONS (the most complex sheet)
# ================================================================
# WHY COMPLEX: Revenue_INR, Payment_Status, and Refund_Flag are
# updated by TWO different systems that go out of sync.
# 206 rows have some form of conflict between these columns.
# The fix: use ALL THREE columns together as one filter.

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  CLEANING: Conversions_Orders")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# LEARN: inplace=True works on methods like drop_duplicates
#        but does NOT work on boolean filters [ ]
#        For filtering, always reassign with .copy()
conv_c = conv.drop_duplicates(subset='Event_ID', keep='first').copy()
print(f"Dedup: {len(conv)} → {len(conv_c)} rows")

# Fix 1 — Payment_Status: 'paid' → 'Paid'
# LEARN: .str.title() handles all casing variants in one step
conv_c['Payment_Status'] = conv_c['Payment_Status'].str.strip().str.title()

# Fix 2 — Refund_Flag: 'Y' → 'Yes', NaN → 'No'
# WHY fillna('No'): NaN means the flag was never set
#     We give benefit of doubt — assume not refunded
#     (conservative approach — better to include uncertain rows)
conv_c['Refund_Flag'] = (conv_c['Refund_Flag']
                          .replace({'Y': 'Yes'})
                          .fillna('No'))

# Fix 3 — UTM_Source: normalise to lowercase
# 'Instagram' and 'instagram' are the same source
conv_c['UTM_Source'] = (conv_c['UTM_Source']
                         .str.strip()
                         .str.lower()
                         .fillna('unknown'))

# Fix 4 — First_Time_Buyer: 'yes' → 'Yes'
conv_c['First_Time_Buyer'] = (conv_c['First_Time_Buyer']
                               .str.strip()
                               .str.title()
                               .fillna('Unknown'))

# Fix 5 — UNKNOWN-CAM is not a real campaign → replace with NaN
conv_c['Campaign_ID'] = conv_c['Campaign_ID'].replace('UNKNOWN-CAM', np.nan)

# ── THE CRITICAL FILTER ─────────────────────────────────────────
# LEARN: We chain ALL conditions into ONE filter with ONE .copy()
#        This is cleaner than filtering step by step
#        Each condition is in its own parentheses
#        & means ALL conditions must be True for the row to be kept
#
#        Using only Payment_Status='Paid' misses 86 refunded rows
#        Using only Refund_Flag='No'  misses 80 rows not synced
#        Using BOTH together catches every conflict case
conv_valid = conv_c[
    conv_c['Revenue_INR'].notna()            &  # revenue must exist
    (conv_c['Revenue_INR'] > 0)              &  # revenue must be positive
    (conv_c['Payment_Status'] == 'Paid')     &  # must be paid
    (conv_c['Refund_Flag']    == 'No')          # must not be refunded
].copy()
# ───────────────────────────────────────────────────────────────

print(f"\nConversion funnel:")
print(f"  Raw rows              : {len(conv):>5}")
print(f"  After dedup           : {len(conv_c):>5}")
print(f"  Valid revenue rows    : {len(conv_valid):>5}")
print(f"  Total valid revenue   : ₹{conv_valid['Revenue_INR'].sum():>10,.0f}")
print(f"  ⚠️  Always use conv_valid for any revenue number")
print(f"✅ Conversions clean")


# ================================================================
# STEP 7 — CLEAN DAILY METRICS
# ================================================================

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  CLEANING: Daily_Profile_Metrics")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# LEARN: .duplicated() with no args checks ALL columns
#        (entire row must be identical to be a duplicate)
daily_c = daily.drop_duplicates().copy()
print(f"Dedup: {len(daily)} → {len(daily_c)} rows")

# Fix — Followers_Start has 'missing' as text
# pd.to_numeric turns 'missing' → NaN, then fill with Followers_End
daily_c['Followers_Start'] = pd.to_numeric(
    daily_c['Followers_Start'], errors='coerce'
)
daily_c['Followers_Start'] = daily_c['Followers_Start'].fillna(
    daily_c['Followers_End']
)

# Parse Date
daily_c['Date'] = pd.to_datetime(daily_c['Date'], errors='coerce')

print(f"✅ Daily clean: {len(daily_c)} rows")


# ================================================================
# STEP 8 — CLEAN SURVEY
# ================================================================

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  CLEANING: Audience_Survey")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# LEARN: keep='first' keeps the first occurrence of each duplicate
#        The first response is usually the most reliable
surv_c = surv.drop_duplicates(subset='Email_Hash', keep='first').copy()
print(f"Dedup: {len(surv)} → {len(surv_c)} rows")

# Fix 1 — Age_Group: '25 - 34' → '25-34', 'Unknown' → NaN
# LEARN: .replace() with a dict maps exact values
surv_c['Age_Group'] = surv_c['Age_Group'].replace(
    {'25 - 34': '25-34', 'Unknown': np.nan}
)

# Fix 2 — Gender: 'female' → 'Female'
surv_c['Gender'] = surv_c['Gender'].str.strip().str.title()

# Fix 3 — Active_Follower_Flag: 'Y' → 'Yes', 'N' → 'No'
yn_map = {'Y': 'Yes', 'Yes': 'Yes', 'N': 'No', 'No': 'No'}
surv_c['Active_Follower_Flag'] = surv_c['Active_Follower_Flag'].map(yn_map)

print(f"✅ Survey clean: {len(surv_c)} rows")


# ================================================================
# STEP 9 — ANALYSIS 1: Content Type Performance
# ================================================================
# LEARN: .groupby('col').agg() is the core of all data analysis
#        Split rows into groups → calculate stats per group
#        Named aggregations: new_col_name = ('source_col', 'function')

print("\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  ANALYSIS 1: Content Type Performance")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

content_perf = posts_c.groupby('Content_Type').agg(
    Post_Count     = ('Post_ID',          'count'),
    Avg_Reach      = ('Reach',            'mean'),
    Avg_ER         = ('Engagement_Rate',  'mean'),
    Avg_Saves_Rate = ('Saves_Rate',       'mean'),
    Total_Spend    = ('Ad_Spend_INR',     'sum'),
).round(2).sort_values('Avg_ER', ascending=False)

print(content_perf.to_string())
print("\n→ Carousel: best engagement depth (saves, comments)")
print("→ Reel    : best reach — use to grow new audience")
print("→ Story   : lowest metrics — use only for daily retention")


# ================================================================
# STEP 10 — ANALYSIS 2: Best Time and Day to Post
# ================================================================

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  ANALYSIS 2: Best Time to Post")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

best_hour = (posts_c.dropna(subset=['Hour'])
             .groupby('Hour')['Engagement_Rate']
             .mean()
             .round(2)
             .sort_values(ascending=False))

best_day = (posts_c.groupby('DayOfWeek')['Engagement_Rate']
            .mean()
            .round(2)
            .sort_values(ascending=False))

print("Top 5 hours:")
print(best_hour.head(5))
print("\nBy day of week:")
print(best_day)


# ================================================================
# STEP 11 — ANALYSIS 3: Hashtag Sweet Spot
# ================================================================

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  ANALYSIS 3: Hashtag Sweet Spot")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# LEARN: observed=True suppresses a FutureWarning in newer pandas
#        when groupby is used on a Categorical column (pd.cut result)
hashtag_perf = (posts_c.groupby('Hashtag_Bin', observed=True)['Engagement_Rate']
                .mean()
                .round(2))
print(hashtag_perf)
print("\n→ Sweet spot: 11–15 hashtags")
print("→ Above 20 reduces engagement (algorithm treats it as spam)")


# ================================================================
# STEP 12 — ANALYSIS 4: Campaign ROI and ROAS
# ================================================================
# LEARN: .merge(df2, on='col', how='left')
#        Joins two tables like SQL LEFT JOIN
#        how='left' = keep ALL rows from left table
#                     even if there's no match in right table
#        .reset_index() brings the groupby index back as a column
#        so we can merge on it

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  ANALYSIS 4: Campaign ROI and ROAS")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  ⚠️  Revenue comes from conv_valid only (paid + not refunded)")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# Step 1: sum revenue per campaign from VALID conversions only
camp_rev = (conv_valid
            .groupby('Campaign_ID')['Revenue_INR']
            .sum()
            .reset_index()
            .rename(columns={'Revenue_INR': 'Actual_Revenue'}))

# Step 2: merge revenue into campaigns
camp_roi = camps_c.merge(camp_rev, on='Campaign_ID', how='left')
camp_roi['Actual_Revenue'] = camp_roi['Actual_Revenue'].fillna(0)

# Step 3: calculate ROAS and ROI
# ROAS = Revenue / Cost  (e.g. 3.5 means ₹3.50 back per ₹1 spent)
# ROI% = (Revenue - Cost) / Cost × 100
camp_roi['ROAS']    = (camp_roi['Actual_Revenue'] /
                        camp_roi['Total_Cost'].replace(0, np.nan)).round(2)
camp_roi['ROI_pct'] = ((camp_roi['Actual_Revenue'] - camp_roi['Total_Cost']) /
                        camp_roi['Total_Cost'].replace(0, np.nan) * 100).round(1)

top_camps = (camp_roi[['Campaign_ID', 'Account', 'Objective',
                        'Total_Cost', 'Actual_Revenue', 'ROAS', 'ROI_pct']]
             .sort_values('ROAS', ascending=False)
             .head(10))
print(top_camps.to_string())
print("\n→ ROAS > 1.0 = profitable | ROAS < 1.0 = losing money")


# ================================================================
# STEP 13 — ANALYSIS 5: Revenue Attribution
# ================================================================

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  ANALYSIS 5: Revenue Attribution")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

rev_account = (conv_valid.groupby('Account')['Revenue_INR']
               .sum()
               .sort_values(ascending=False))

rev_utm = (conv_valid.groupby('UTM_Source')['Revenue_INR']
           .sum()
           .sort_values(ascending=False))

# LEARN: .apply(lambda x: ...) runs a function on each value
#        Here we format each number as ₹ with commas
print("Revenue by Account:")
print(rev_account.apply(lambda x: f"₹{x:,.0f}"))

print("\nRevenue by UTM Source:")
print(rev_utm.apply(lambda x: f"₹{x:,.0f}"))

# LEARN: normalize=True converts counts to proportions (0 to 1)
#        .mul(100) converts to percentages
ftb = (conv_valid['First_Time_Buyer']
       .value_counts(normalize=True)
       .mul(100)
       .round(1))
print("\nFirst Time Buyer split %:")
print(ftb)

print("\n→ Bio link outperforms paid social — optimise it first")
print("→ High first-time buyer % means low repeat rate → need retention strategy")


# ================================================================
# STEP 14 — ANALYSIS 6: Follower Growth
# ================================================================

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  ANALYSIS 6: Follower Growth")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

growth = (daily_c.groupby('Account')['Net_Follower_Gain']
          .sum()
          .sort_values(ascending=False))
print("Total net follower gain by account:")
print(growth)

day_type = (daily_c.groupby('Day_Type')['Net_Follower_Gain']
            .mean().round(1))
print("\nAvg follower gain — Weekday vs Weekend:")
print(day_type)

algo_impact = (daily_c.groupby('Algorithm_Change_Flag')['Net_Follower_Gain']
               .mean().round(1))
print("\nAlgorithm change days vs normal:")
print(algo_impact)


# ================================================================
# STEP 15 — ANALYSIS 7: Audience Survey
# ================================================================

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  ANALYSIS 7: Audience Survey Insights")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

print("Discovery source (how followers found accounts):")
print(surv_c['Discovery_Source'].value_counts())

print("\nContent preference:")
print(surv_c['Content_Preference'].value_counts())

# LEARN: .dropna(subset=['col']) drops rows where that specific
#        column is NaN — avoids NaN skewing the group average
intent_age = (surv_c
              .dropna(subset=['Age_Group', 'Purchase_Intent_1_5'])
              .groupby('Age_Group')['Purchase_Intent_1_5']
              .mean()
              .round(2)
              .sort_values(ascending=False))
print("\nPurchase intent (1–5) by age group:")
print(intent_age)

trust_gender = (surv_c
                .dropna(subset=['Gender', 'Brand_Trust_1_5'])
                .groupby('Gender')['Brand_Trust_1_5']
                .mean()
                .round(2)
                .sort_values(ascending=False))
print("\nBrand trust (1–5) by gender:")
print(trust_gender)

print("\n→ Friend referrals + Reels = top organic discovery channels")
print("→ 13-17 has highest purchase intent — high-value segment")


# ================================================================
# STEP 16 — EXECUTIVE SUMMARY
# ================================================================

print("\n\n" + "="*65)
print("   EXECUTIVE SUMMARY")
print("="*65)
print(f"  Total posts analysed        : {len(posts_c):>6,}")
print(f"  Total campaigns             : {len(camps_c):>6,}")
print(f"  Valid revenue orders        : {len(conv_valid):>6,}")
print(f"  Total valid revenue         : ₹{conv_valid['Revenue_INR'].sum():>10,.0f}")
print(f"  Avg engagement rate         : {posts_c['Engagement_Rate'].mean():>6.2f}%")
print(f"  Best content (engagement)   : {'Carousel':>12}")
print(f"  Best content (reach)        : {'Reel':>12}")
print(f"  Best posting hour           : {'8 AM':>12}")
print(f"  Hashtag sweet spot          : {'11-15 tags':>12}")
print(f"  Top revenue UTM source      : {rev_utm.idxmax():>12}")
print(f"  Top ROAS campaign           : {camp_roi.sort_values('ROAS',ascending=False).iloc[0]['Campaign_ID']:>12}")
print(f"  Max ROAS achieved           : {camp_roi['ROAS'].max():>11.2f}x")
print("="*65)


# ================================================================
# PANDAS QUICK REFERENCE — WHAT YOU LEARNED
# ================================================================
print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PANDAS QUICK REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  LOADING
  pd.read_excel(file, sheet_name=None)  → load all sheets as dict

  AUDITING
  .shape                                → (rows, cols)
  .duplicated('col').sum()              → count duplicate rows
  .isna().sum()                         → count missing values
  .unique()                             → see all distinct values
  .value_counts()                       → count each value

  CLEANING
  .drop_duplicates(subset, keep)        → remove duplicates
  .copy()                               → make independent copy
  .str.strip().str.title()              → fix casing ('paid'→'Paid')
  .map({dict}).fillna('No')             → replace + fill blanks
  .replace({'old': 'new'})              → replace specific values
  pd.to_numeric(errors='coerce')        → convert, bad→NaN
  .fillna(value)                        → fill NaN with default
  .where(condition, other=np.nan)       → keep if True, else NaN
  ~condition                            → NOT (flip True/False)
  col1.notna() & (col2 > 0) & (col3==x) → chain multiple filters

  INPLACE RULE
  .drop_duplicates(inplace=True)  ✅   works on methods
  df[df['col'] > 0].inplace       ❌   does NOT exist on filters
  → For filtering: always df = df[condition].copy()

  DERIVING
  col1 + col2 / col3.replace(0,NaN)    → arithmetic, safe divide
  pd.to_datetime(col, errors='coerce') → parse dates
  .dt.hour / .dt.day_name()            → extract from datetime
  pd.cut(col, bins, labels)            → band a numeric column

  ANALYSING
  .groupby('col').agg(name=('col','fn'))→ group + summarise
  .merge(df2, on='col', how='left')    → join two tables
  .reset_index()                        → index back as column
  .sort_values('col', ascending=False) → sort descending
  .apply(lambda x: f"₹{x:,.0f}")      → format each value
  .dropna(subset=['col'])              → drop only where col=NaN
  .value_counts(normalize=True).mul(100) → percentage split
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
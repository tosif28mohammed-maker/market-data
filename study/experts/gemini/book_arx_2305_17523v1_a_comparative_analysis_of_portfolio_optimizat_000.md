# A Comparative Analysis of Portfolio Optimization Using Mean-Variance, Hierarchical Risk Parity, and Reinforcement Learning Approaches on the Indian Stock Market
स्रोत: book: arx_2305_17523v1_a_comparative_analysis_of_portfolio_optimizat.txt · arx_2305_17523v1_a_comparative_analysis_of_portfolio_optimizat.txt · Gemini ने पढ़ा 2026-11-23 09:47 UTC

## Point-by-point
- Yeh research report Indian stock market ke 6 sectors (Auto, Pharma, IT, Banking, Finance, FMCG) aur 1 Mixed sector ke top 10 stocks par 3 portfolio optimization techniques (Markowitz MVP, Hierarchical Risk Parity HRP, aur Deep Q-Learning RL) ki tulna karti hai.
- Data period: Training data 17 November 2017 se 30 August 2019 tak daily close prices; Out-of-sample testing data 03 September 2019 se 27 February 2020 tak.
- Markowitz Mean-Variance Portfolio (MVP): Daily returns ka log percentage change nikal kar daily standard deviation ko sqrt(252) se multiply karke annual volatility aur returns nikale gaye. Risk-free rate Rf = 1% maanke Maximum Sharpe ratio portfolio solve kiya gaya.
- Hierarchical Risk Parity (HRP): 3 steps me kaam karta hai - (1) Correlation matrix ko distance matrix D(i,j) = sqrt(0.5*(1 - rho)) aur Euclidean distance matrix D_bar me badal kar single linkage hierarchical clustering se dendrogram banayein. (2) Covariance matrix ko quasi-diagonalize karein. (3) Inverse-variance weight allocation se top-down recursive bisection dwara stock weights w_i = (1/sigma_i^2) / sum(1/sigma_j^2) assign karein.
- Deep Q-Learning (DQN) Reinforcement Learning Setup: State = specific rolling window size par stocks ka correlation matrix; Action = portfolio me stock weights badalna (Buy, Sell, Hold); Reward = portfolio ka Sharpe Ratio.
- Out-of-sample Testing Results (Sharpe Ratio comparison): RL portfolio ne lagbhag sabhi sectors me MVP, HRP aur Equal-Weight portfolios ko pachaad diya:
- - Auto Sector: RL (2.0812) > HRP (1.3712) > MVP (1.2450) > Equal Weight (-0.6397)
- - Pharma Sector: RL (4.3249) > MVP (4.1720) > HRP (4.0711) > Equal Weight (-0.3732)
- - Banking Sector: RL (3.3581) > MVP (1.9457) > HRP (1.3009) > Equal Weight (1.5770)
- - Finance Sector: RL (2.0895) > HRP (1.2104) > MVP (0.6464) > Equal Weight (-0.3345)
- - FMCG Sector: RL (1.7219) > MVP (1.6332) > HRP (1.4959) > Equal Weight (1.0233)
- - Mixed Portfolio (10 stocks across 5 sectors): RL (3.4577) > HRP (0.9437) > MVP (0.3440) > Equal Weight (0.1248)
- - Exception (IT Sector): Equal Weight (3.0135) > RL (2.0895) > MVP (1.4834) > HRP (1.1307)

## Niyam
- [new/yes] Deep Q-Network (DQN) Reinforcement Learning Portfolio Allocation Strategy: Rolling window correlation matrix ko state, weight adjustment (Buy/Sell/Hold) ko action, aur Sharpe Ratio ko reward maankar Deep Q-Learning model dwara portfolio rebalance karein. | entry: DQN RL agent ke policy output dwara har periodic rebalancing date par calculated stock weight allocations ko execute karein. | exit: Agli rebalancing period par DQN model ke dwara naye portfolio weight adjustments ke anusar portfolio balance karein. | stop: number nahi diya
- [new/yes] Hierarchical Risk Parity (HRP) Portfolio Asset Allocation: Correlation distance matrix, quasi-diagonalization aur recursive bisection inverse-variance allocation dwara stock portfolio weights assign karein. | entry: Correlation matrix se distance matrix D(i,j) = sqrt(0.5*(1 - rho)) banayein, agglomerative single-linkage clustering se dendrogram banayein, covariance matrix ko quasi-diagonalize karke recursive bisection dwara inverse-variance weights w_i = (1/sigma_i^2) / sum(1/sigma_j^2) allocate karein. | exit: Model rebalance schedule par weights update karein. | stop: number nahi diya
- [new/yes] Markowitz Maximum Sharpe Ratio Optimization Setup: Annualized daily log returns aur annualized covariance matrix (daily std * sqrt(252)) dwara quadratic programming solve karke highest Sharpe ratio portfolio weight w construct karein. | entry: Minimize w^T Σ w subject to w^T μ >= target return aur sum(w) = 1 quadratic optimization solve karke maximum Sharpe ratio (Rc - Rf)/sigma_c allocation execute karein (jahan Rf = 1%). | exit: Scheduled portfolio rebalancing date par weights adjust karein. | stop: number nahi diya

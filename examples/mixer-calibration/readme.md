---
id: index
title: IQ Mixer Calibration - From theory to practice
sidebar_label: IQ Mixer Calibration
slug: ./
---

## IQ Mixer mathematical model

### Up-conversation

#### Ideal Mixer

Suppose we have a local oscillator (LO) with a frequency of $\Omega$, it can be described as:

$$
A_{LO}(t) = \text{Re}\left\{A_0 e^{i \Omega t} \right\}
$$

When we pass it through an ideal IQ mixer, the output will be:

$$
A_{RF}(t) = \text{Re}\left\{z(t) A_0 e^{i \Omega t} \right\} = A_0 \left(z_I(t) \text{cos}(\Omega t) - z_Q(t) \text{sin}(\Omega t)\right) 
$$

With $z(t)$ is defined according to the inputs at the I & Q ports:

$$
z(t) = z_I(t) + i z_Q(t)
$$

------------------------------------------------------------
> **_Example:_** : 
> It is common have $z_I(t) = \text{cos} \left( \omega_{IF} t + \phi \right)$ and $z_Q(t) = \text{sin}\left(\omega_{IF}t + \phi \right)$.
> This makes $z(t) = e^{i (\omega_{IF}t + \phi)}$ and:
>
> $$
> A_{RF}(t) = \text{Re}\left\{A_0 e^{i (\Omega + \omega_{IF}) t + \phi} \right\}
> $$
>
> As can be seen, applying a Cosine & Sine at the I & Q ports will shift the frequency of the LO and add a phase.

----------------------------------------------------------------
Rewriting the equation, and assuming $A_0=1$, we get write:

$$
A_{RF}(t) = \frac{1}{2} \left(z(t) e^{i \Omega t} + z^*(t) e^{-i \Omega t}\right) 
$$

In the frequency domain we can write it in matrix form:

$$
\begin{pmatrix}
a[\omega] \\
a^*[-\omega] 
\end{pmatrix} 
=
\frac{1}{2}
\begin{pmatrix}
1 & 0 \\
0 & 1 
\end{pmatrix}
\begin{pmatrix}
z[\omega+\Omega] \\
z^*[\omega-\Omega] 
\end{pmatrix}
$$

When we defined $A_{RF}[\omega] = a[\omega] + a^*[-\omega]$.
Note that generally speaking, this creates two sidebands at the two sides of $\Omega$. 
We will treat the upper sideband as the signal, and the lower as the image, which can be removed by a proper choice of $z(t)$.

------------------------------------------------------------
> **_Example:_** : 
> Looking back at the previous example (without the phase): 
> 
> $$
> z(t) = e^{i \omega_{IF}t} \rightarrow z[\omega] = \delta[\omega+\omega_{IF}]
> $$
> $$
> z^*(t) = e^{-i \omega_{IF}t} \rightarrow z^*[\omega] = \delta[\omega - \omega_{IF}]
> $$
> $$
> A_{RF}[\omega] = \frac{1}{2} \left(\delta[\omega+(\Omega+\omega_{IF})] + \delta[\omega-(\Omega+\omega_{IF})]\right)
> $$ 
> $$
> A_{RF}(t) = \text{cos} \left((\Omega+\omega_{IF})t\right)
> $$
> The choice above removed the image sideband and kept only the signal sideband.

----------------------------------------------------------------

#### Non-ideal Mixer
The math we described above arise from the mixing of two branches:

1. The signal at the I port is multiplied by the cosine of the LO
2. The signal at the Q port is multiplied by the sine of the LO

In an ideal mixer, it is assumed that these two branches are identical both in amplitude and in phase. When the mixer is not ideal this can be modeled as:

$$
A_{RF}(t) = \text{Re}\left\{z(t) A_0 \left[\text{cos}(\Omega t) + i r \text{sin}(\Omega t+\phi) \right] \right\}
$$

Where $r$ and $\phi$ are the relative amplitude and phase mismatch between the two branches. Note that $r=1$ and $\phi=0$ restore the ideal mixer equation.

In addition to the branches' imbalance, non-ideal mixers also have LO leakage which can be modeled as:

$$
A_{RF}(t) = \text{Re}\left\{z(t) A_0 \left[\text{cos}(\Omega t) + i r \text{sin}(\Omega t+\phi) \right] + \epsilon A_0 e^{i \Omega t} \right\}
$$

In the frequency domain, this takes the form of:

$$
\begin{pmatrix}
a[\omega] \\
a^*[-\omega] 
\end{pmatrix} 
=
\frac{1}{4}
\begin{pmatrix}
d^* & o \\
o^* & d 
\end{pmatrix}
\begin{pmatrix}
z[\omega+\Omega] \\
z^*[\omega-\Omega] 
\end{pmatrix}
+
\frac{\epsilon}{2}
\begin{pmatrix}
\delta[\omega + \Omega] \\
\delta[\omega - \Omega] 
\end{pmatrix}
$$

With $d = 1 + r e^ {-i \phi}$ and $o = 1 - r e^ {i \phi}$.

Note that the non-ideal mixer will have leakage terms at $\Omega$ and at the image sideband. 
Adding a constant term to $z(t)$ can cancel the LO leakage term.
Applying the appropriate gain and phase offsets to the I & Q channels can remove the image term.

The notation so far was best for having an intuitive understanding of the effects of imbalance. However, it is easier to follow a slightly different notation, for the actual correction.
We will treat the imbalance as having a symmetric effect directly on the I & Q inputs, such that:
$$
\begin{pmatrix}
\tilde{z}_I(t) \\
\tilde{z}_Q(t)
\end{pmatrix}
=
\begin{pmatrix}
(1+\varepsilon_a) \text{cos}(\varepsilon_\phi) & - (1+\varepsilon_a) \text{sin}(\varepsilon_\phi) \\
- (1-\varepsilon_a) \text{sin}(\varepsilon_\phi) & (1-\varepsilon_a) \text{cos}(\varepsilon_\phi)
\end{pmatrix}
\begin{pmatrix}
z_I(t) \\
z_Q(t)
\end{pmatrix}
$$

With $\varepsilon_a$ and $\varepsilon_\phi$ being the amplitude and phase imbalances.
In order to correct the imbalance, we need to multiply $z$ by a correction matrix that will cancel the imbalance matrix. The correction matrix can be calculated by taking the inverse of the imbalance matrix:

$$
\frac{1}{\left( 1-\varepsilon_a^2 \right) \left( 2 \text{cos}^2(\varepsilon_\phi) - 1 \right)}
\begin{pmatrix}
(1-\varepsilon_a) \text{cos}(\varepsilon_\phi) & (1+\varepsilon_a) \text{sin}(\varepsilon_\phi) \\
(1-\varepsilon_a) \text{sin}(\varepsilon_\phi) & (1+\varepsilon_a) \text{cos}(\varepsilon_\phi)
\end{pmatrix} 
$$

While the matrix has four elements, it is only dependent on the two imbalance parameters. 
There is a function named 'IQ_imbalance_correction' which takes these two parameters and calculates the above matrix.

### Down-conversation

The ideal behavior of an IQ mixer used for down-conversion is:

With $z(t)$ is defined according to the inputs at the I & Q ports according to:

$$
z(t) = z_I(t) + i z_Q(t) = \text{LPF}\left\{A_{RF}(t) e^{-i \Omega t} \right\}
$$

Where 'LPF' indicates a Low Pass Filter. The imbalance comes similarly:

$$
\tilde{z}(t) = \tilde{z}_I(t) + i \tilde{z}_Q(t) = \text{LPF}\left\{A_{RF}(t) \left[2 (1+\varepsilon_a)\text{cos}(\Omega t-\varepsilon_\phi) + 2 i (1-\varepsilon_a) \text{sin}(\Omega t+\varepsilon_\phi) \right] \right\}
$$

The transformation from $z$ to $\tilde{z}$ can be represented by the following imbalance matrix:

$$
\begin{pmatrix}
\tilde{z}_I(t) \\
\tilde{z}_Q(t)
\end{pmatrix}
=
\begin{pmatrix}
(1+\varepsilon_a) \text{cos}(\varepsilon_\phi) & (1+\varepsilon_a) \text{sin}(\varepsilon_\phi) \\
- (1-\varepsilon_a) \text{sin}(\varepsilon_\phi) & - (1-\varepsilon_a) \text{cos}(\varepsilon_\phi)
\end{pmatrix}
\begin{pmatrix}
z_I(t) \\
z_Q(t)
\end{pmatrix}
$$
  
Which can be further decomposed as:

$$
\begin{pmatrix}
(1+\varepsilon_a) \text{cos}(\varepsilon_\phi) & (1+\varepsilon_a) \text{sin}(\varepsilon_\phi) \\
- (1-\varepsilon_a) \text{sin}(\varepsilon_\phi) & - (1-\varepsilon_a) \text{cos}(\varepsilon_\phi)
\end{pmatrix}
=
\underbrace{\begin{pmatrix}
1 & \text{tan}(\varepsilon_\phi) \\
\text{tan}(\varepsilon_\phi) & 1
\end{pmatrix}}_{\text{Leakage}}
\underbrace{\begin{pmatrix}
(1+\varepsilon_a) \text{cos}(\varepsilon_\phi) & 0 \\
0 & - (1-\varepsilon_a) \text{cos}(\varepsilon_\phi)
\end{pmatrix}}_{\text{Scaling}}
$$
  
We can see that the matrix can be decomposed into two terms: The 1st which causes the leakage between the sidebands and a 2nd which only scales the results.
We can ignore the 2nd term as the scaling is not important for practical applications. Furthermore, we note that the leakage term only depends on a single parameter $\text{tan}(\varepsilon_\phi)$.
The inverse leakage matrix is given by:

$$
\begin{pmatrix}
-1 & \text{tan}(\varepsilon_\phi) \\
\text{tan}(\varepsilon_\phi) & -1
\end{pmatrix}
$$

The normalization by the determinant was also ignored as it only scales the data.

In order to correct the down-conversation we only need to multiply $\tilde{z}$ by the inverse matrix:

 $$
\begin{pmatrix}
z_I(t) \\
z_Q(t)
\end{pmatrix}
=
N
\begin{pmatrix}
-1 & \text{tan}(\varepsilon_\phi) \\
\text{tan}(\varepsilon_\phi) & -1
\end{pmatrix}
\begin{pmatrix}
\tilde{z}_I(t) \\
\tilde{z}_Q(t)
\end{pmatrix}
$$

Where $N$ is a diagonal matrix which we ignore.

## Scripts for mixer calibration

[Manual Up-conversation Calibration](manual_mixer_calibration.py) - This scripts shows the basic commands used to calibrate the IQ mixer.
The calibration should be done by connecting the output of the mixer to a spectrum analyzer and minimizing the LO leakage term at $\Omega$ and image term at $\Omega-\omega_{IF}$.
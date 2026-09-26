@documenttitle{Physics, banner = https://upload.wikimedia.org/wikipedia/commons/3/31/Portal_Math_Banner_Background_ka.jpg}
@folder{Electromagnetism}
@author{Vivek Sharma}
@date{26 September 2026}
@title{The Electromagnetic Lagrangian}
@tags{Field theory, Electromagnetism, Lagrangian mechanics}

@button{Home, href = /, color = black}
@button{GitHub, href = https://github.com/VivekH90/mark-two, color = #4f6fd8}
@button{About, href = /about, color = #4f9d69}
@gallery{source = NASA, query = electromagnetic fields, count = 7}

@begin(section){Setting up the field, label = setting-up-the-field}
We work in flat spacetime with metric signature ((+,-,-,-)), and treat the electromagnetic four-potential (A^mu) as the dynamical field.

[
F_{mu
u}=partial_mu A_
u-partial_
u A_mu.
]

@begin(definition){Field strength tensor, label = field-strength}
Given a four-potential (A^mu), the field-strength tensor is
[
F_{mu
u}:=partial_mu A_
u-partial_
u A_mu.
]
@end(definition)

@begin(subsection){Gauge invariance, label = gauge-invariance}
The transformation (A_mumapsto A_mu+partial_muchi) leaves (F_{mu
u}) unchanged.

@begin(axiom){Gauge freedom, label = gauge-freedom}
Two gauge-related potentials describe the same electromagnetic configuration.
@end(axiom)
@end(subsection)
@end(section)

@begin(section){The Lagrangian density, label = lagrangian-density}
We want a Lorentz scalar whose variation gives the field equations.
[
mathcal L_{mathrm{EM}}=-rac14F_{mu
u}F^{mu
u}-j^mu A_mu.
]

@begin(remark){The point of the construction}
The first term describes the free field. The second couples it to its source.
@end(remark)
@end(section)

@begin(section){Euler-Lagrange equations, label = euler-lagrange}
Treat (A_mu) as the dynamical variable and apply the field Euler-Lagrange equation.
[
partial_
uleft(rac{partialmathcal L}{partial(partial_
u A_mu)}ight)-rac{partialmathcal L}{partial A_mu}=0.
]

@begin(proposition){Maxwell's inhomogeneous equations, label = maxwell-equations}
Varying the electromagnetic Lagrangian gives
[
partial_mu F^{mu
u}=j^
u.
]
@end(proposition)

@begin(proof)
The kinetic term differentiates to the field tensor after using antisymmetry. Substitution gives
[
partial_mu F^{mu
u}=j^
u.
]
@end(proof)
@end(section)

@begin(section){References, label = references}
The same formalism appears in standard field theory and electrodynamics texts.

@begin(enumerate)
@item{J. D. Jackson, Classical Electrodynamics, 3rd ed.}
@item{M. E. Peskin and D. V. Schroeder, An Introduction to Quantum Field Theory.}
@end(enumerate)
@end(section)

@relatedlinks{Electromagnetism notes, href = /physics/electromagnetism}
@relatedlinks{Lagrangian mechanics, href = /physics/classical-mechanics/lagrangian}
